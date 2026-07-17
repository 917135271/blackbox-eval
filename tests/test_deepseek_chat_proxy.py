from __future__ import annotations

import importlib.util
import json
import unittest
from http.client import IncompleteRead
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "candidates" / "codex" / "deepseek_chat_proxy.py"
SPEC = importlib.util.spec_from_file_location("deepseek_chat_proxy", MODULE_PATH)
assert SPEC and SPEC.loader
PROXY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROXY)


class ResponsesAdapterTest(unittest.TestCase):
    def test_retries_incomplete_upstream_response(self) -> None:
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self) -> bytes:
                return b'{"choices": [], "usage": {}}'

        with mock.patch.dict(
            PROXY.os.environ,
            {"LLM_API_KEY": "test-only", "CODEX_PROXY_MAX_RETRIES": "1"},
        ), mock.patch.object(
            PROXY,
            "urlopen",
            side_effect=[IncompleteRead(b""), Response()],
        ) as upstream, mock.patch.object(PROXY.time, "sleep") as sleep:
            result = PROXY._deepseek_request({"model": "test"}, None)

        self.assertEqual(result["choices"], [])
        self.assertEqual(upstream.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_translates_responses_history_and_tools(self) -> None:
        payload = {
            "model": "deepseek-v4-pro",
            "instructions": "Use evidence.",
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "check invoice"}],
                },
                {
                    "type": "function_call",
                    "call_id": "call_1",
                    "name": "lookup",
                    "arguments": "{\"invoice\":\"A1\"}",
                },
                {
                    "type": "function_call_output",
                    "call_id": "call_1",
                    "output": "{\"count\":2}",
                },
            ],
            "tools": [
                {
                    "type": "function",
                    "name": "lookup",
                    "description": "Lookup an invoice.",
                    "parameters": {
                        "type": "object",
                        "properties": {"invoice": {"type": "string"}},
                        "required": ["invoice"],
                    },
                }
            ],
        }

        chat, metadata = PROXY.responses_to_chat(payload)

        self.assertEqual(chat["messages"][0], {"role": "system", "content": "Use evidence."})
        self.assertEqual(chat["messages"][1]["content"], "check invoice")
        self.assertEqual(chat["messages"][2]["tool_calls"][0]["id"], "call_1")
        self.assertEqual(chat["messages"][3]["tool_call_id"], "call_1")
        self.assertEqual(chat["tools"][0]["function"]["name"], "lookup")
        self.assertEqual(metadata["lookup"]["type"], "function")

    def test_translates_namespaced_tool(self) -> None:
        payload = {
            "input": [],
            "tools": [
                {
                    "type": "namespace",
                    "name": "expense_query",
                    "tools": [
                        {
                            "type": "function",
                            "name": "find_invoice_usage",
                            "parameters": {"type": "object", "properties": {}},
                        }
                    ],
                }
            ],
        }

        chat, metadata = PROXY.responses_to_chat(payload)

        wire_name = "expense_query__find_invoice_usage"
        self.assertEqual(chat["tools"][0]["function"]["name"], wire_name)
        self.assertEqual(metadata[wire_name]["namespace"], "expense_query")

    def test_translates_output_schema_to_json_mode(self) -> None:
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
            "additionalProperties": False,
        }
        payload = {
            "input": [],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "codex_output_schema",
                    "strict": True,
                    "schema": schema,
                }
            },
        }

        chat, _ = PROXY.responses_to_chat(payload)

        self.assertEqual(chat["response_format"], {"type": "json_object"})
        self.assertIn(json.dumps(schema, ensure_ascii=False, separators=(",", ":")), chat["messages"][0]["content"])

    def test_translates_chat_tool_call_to_responses_event(self) -> None:
        response = {
            "id": "chat_1",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_9",
                                "type": "function",
                                "function": {
                                    "name": "lookup",
                                    "arguments": "{\"invoice\":\"A1\"}",
                                },
                            }
                        ],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        }

        events = PROXY.chat_response_to_events(response, {"lookup": {"type": "function", "name": "lookup", "namespace": ""}})

        self.assertEqual(events[0]["type"], "response.created")
        self.assertEqual(events[1]["item"]["type"], "function_call")
        self.assertEqual(events[1]["item"]["call_id"], "call_9")
        self.assertEqual(events[-1]["response"]["usage"]["total_tokens"], 14)

    def test_recovers_unique_namespace_when_model_strips_tool_prefix(self) -> None:
        response = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_10",
                                "function": {"name": "list_expenses", "arguments": "{}"},
                            }
                        ]
                    }
                }
            ]
        }
        metadata = {
            "expense_query__list_expenses": {
                "type": "function",
                "name": "list_expenses",
                "namespace": "expense_query",
            }
        }

        events = PROXY.chat_response_to_events(response, metadata)

        call = events[1]["item"]
        self.assertEqual(call["name"], "list_expenses")
        self.assertEqual(call["namespace"], "expense_query")

    def test_does_not_guess_namespace_for_ambiguous_bare_tool_name(self) -> None:
        response = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_11",
                                "function": {"name": "lookup", "arguments": "{}"},
                            }
                        ]
                    }
                }
            ]
        }
        metadata = {
            "first__lookup": {"type": "function", "name": "lookup", "namespace": "first"},
            "second__lookup": {"type": "function", "name": "lookup", "namespace": "second"},
        }

        events = PROXY.chat_response_to_events(response, metadata)

        call = events[1]["item"]
        self.assertEqual(call["name"], "lookup")
        self.assertNotIn("namespace", call)

    def test_normalize_messages_inserts_missing_tool_output(self) -> None:
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_missing",
                        "type": "function",
                        "function": {"name": "lookup", "arguments": "{}"},
                    }
                ],
            }
        ]

        normalized = PROXY.normalize_messages(messages)

        self.assertEqual(normalized[1]["role"], "tool")
        self.assertEqual(normalized[1]["tool_call_id"], "call_missing")
        self.assertEqual(json.loads(normalized[1]["content"]), {})


if __name__ == "__main__":
    unittest.main()
