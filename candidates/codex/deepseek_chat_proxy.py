from __future__ import annotations

import json
import os
import time
import uuid
from http.client import IncompleteRead
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEEPSEEK_CHAT_URL = os.environ.get(
    "DEEPSEEK_CHAT_URL", "https://api.deepseek.com/v1/chat/completions"
)


def normalize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize Chat Completions history for DeepSeek's stricter tool ordering."""
    normalized: list[dict[str, Any]] = []
    skip: set[int] = set()
    for index, raw_message in enumerate(messages):
        if index in skip:
            continue
        message = dict(raw_message)
        if message.get("role") == "developer":
            message["role"] = "system"
        normalized.append(message)

        tool_calls = message.get("tool_calls") if message.get("role") == "assistant" else None
        if not tool_calls:
            continue

        expected_ids = [
            tool_call.get("id")
            for tool_call in tool_calls
            if isinstance(tool_call, dict) and tool_call.get("id")
        ]
        added_ids: set[str] = set()
        for lookahead_index in range(index + 1, len(messages)):
            candidate = messages[lookahead_index]
            if candidate.get("role") != "tool":
                continue
            tool_call_id = candidate.get("tool_call_id")
            if tool_call_id in expected_ids and tool_call_id not in added_ids:
                normalized.append(dict(candidate))
                skip.add(lookahead_index)
                added_ids.add(tool_call_id)
            if len(added_ids) == len(expected_ids):
                break

        for missing_id in expected_ids:
            if missing_id not in added_ids:
                normalized.append(
                    {
                        "role": "tool",
                        "tool_call_id": missing_id,
                        "content": "{}",
                    }
                )

    return normalized


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") in {"input_text", "output_text", "text"}:
            parts.append(str(item.get("text", "")))
    return "\n".join(part for part in parts if part)


def _tool_output_text(output: Any) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, dict) and isinstance(output.get("content"), str):
        return output["content"]
    if isinstance(output, list):
        text = _content_text(output)
        if text:
            return text
    return json.dumps(output, ensure_ascii=False)


def _append_function_call(
    messages: list[dict[str, Any]], call_id: str, name: str, arguments: str
) -> None:
    call = {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }
    if messages and messages[-1].get("role") == "assistant" and messages[-1].get("tool_calls"):
        messages[-1]["tool_calls"].append(call)
    else:
        messages.append({"role": "assistant", "content": None, "tool_calls": [call]})


def responses_to_chat(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    """Translate one OpenAI Responses request into DeepSeek Chat Completions."""
    messages: list[dict[str, Any]] = []
    instructions = payload.get("instructions")
    if isinstance(instructions, str) and instructions.strip():
        messages.append({"role": "system", "content": instructions})

    text_config = payload.get("text")
    text_format = text_config.get("format") if isinstance(text_config, dict) else None
    output_schema: dict[str, Any] | None = None
    if isinstance(text_format, dict) and text_format.get("type") == "json_schema":
        schema = text_format.get("schema")
        if isinstance(schema, dict):
            output_schema = schema
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Return the final answer as one JSON object and no surrounding text. "
                        "The JSON must match this schema: "
                        + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
                    ),
                }
            )

    for item in payload.get("input") or []:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "message":
            role = str(item.get("role") or "user")
            if role == "developer":
                role = "system"
            messages.append({"role": role, "content": _content_text(item.get("content"))})
        elif item_type in {"function_call", "custom_tool_call"}:
            arguments = item.get("arguments", item.get("input", "{}"))
            if not isinstance(arguments, str):
                arguments = json.dumps(arguments, ensure_ascii=False)
            _append_function_call(
                messages,
                str(item.get("call_id") or item.get("id") or f"call_{uuid.uuid4().hex}"),
                str(item.get("name") or "unknown_tool"),
                arguments,
            )
        elif item_type in {"function_call_output", "custom_tool_call_output"}:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": str(item.get("call_id") or ""),
                    "content": _tool_output_text(item.get("output", "")),
                }
            )

    translated_tools: list[dict[str, Any]] = []
    tool_metadata: dict[str, dict[str, str]] = {}

    def add_tool(tool: dict[str, Any], namespace: str | None = None) -> None:
        name = str(tool.get("name") or "")
        if not name:
            return
        wire_name = f"{namespace}__{name}" if namespace else name
        original_type = str(tool.get("type") or "function")
        parameters = tool.get("parameters")
        if not isinstance(parameters, dict):
            parameters = {
                "type": "object",
                "properties": {"input": {"type": "string"}},
                "required": ["input"],
                "additionalProperties": False,
            }
        translated_tools.append(
            {
                "type": "function",
                "function": {
                    "name": wire_name,
                    "description": str(tool.get("description") or ""),
                    "parameters": parameters,
                },
            }
        )
        tool_metadata[wire_name] = {
            "type": original_type,
            "name": name,
            "namespace": namespace or "",
        }

    for tool in payload.get("tools") or []:
        if not isinstance(tool, dict):
            continue
        if tool.get("type") == "namespace" and isinstance(tool.get("tools"), list):
            for child in tool["tools"]:
                if isinstance(child, dict):
                    add_tool(child, str(tool.get("name") or ""))
        else:
            add_tool(tool)

    chat: dict[str, Any] = {
        "model": payload.get("model") or "deepseek-v4-pro",
        "messages": normalize_messages(messages),
        "stream": False,
    }
    if translated_tools:
        chat["tools"] = translated_tools
        if payload.get("tool_choice") in {"auto", "none", "required"}:
            chat["tool_choice"] = payload["tool_choice"]
    if isinstance(payload.get("temperature"), (int, float)):
        chat["temperature"] = payload["temperature"]
    if output_schema is not None:
        chat["response_format"] = {"type": "json_object"}
    max_tokens = payload.get("max_output_tokens")
    if isinstance(max_tokens, int) and max_tokens > 0:
        chat["max_tokens"] = max_tokens
    return chat, tool_metadata


def chat_response_to_events(
    response: dict[str, Any], tool_metadata: dict[str, dict[str, str]] | None = None
) -> list[dict[str, Any]]:
    """Translate a non-streaming DeepSeek response into Responses SSE events."""
    tool_metadata = tool_metadata or {}
    response_id = str(response.get("id") or f"resp_{uuid.uuid4().hex}")
    events: list[dict[str, Any]] = [
        {"type": "response.created", "response": {"id": response_id}}
    ]
    choices = response.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    content = message.get("content")
    if isinstance(content, str) and content:
        events.append(
            {
                "type": "response.output_item.done",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "id": f"msg_{uuid.uuid4().hex}",
                    "content": [{"type": "output_text", "text": content}],
                },
            }
        )

    for raw_call in message.get("tool_calls") or []:
        if not isinstance(raw_call, dict):
            continue
        function = raw_call.get("function") or {}
        wire_name = str(function.get("name") or "unknown_tool")
        metadata = tool_metadata.get(wire_name, {})
        if not metadata:
            candidates = [
                value
                for key, value in tool_metadata.items()
                if value.get("name") == wire_name or key.endswith(f"__{wire_name}")
            ]
            if len(candidates) == 1:
                metadata = candidates[0]
        call_id = str(raw_call.get("id") or f"call_{uuid.uuid4().hex}")
        arguments = str(function.get("arguments") or "{}")
        if metadata.get("type") == "custom":
            try:
                parsed_arguments = json.loads(arguments)
            except json.JSONDecodeError:
                parsed_arguments = {}
            item: dict[str, Any] = {
                "type": "custom_tool_call",
                "call_id": call_id,
                "name": metadata.get("name", wire_name),
                "input": str(parsed_arguments.get("input", arguments)),
            }
        else:
            item = {
                "type": "function_call",
                "call_id": call_id,
                "name": metadata.get("name", wire_name),
                "arguments": arguments,
            }
        if metadata.get("namespace"):
            item["namespace"] = metadata["namespace"]
        events.append({"type": "response.output_item.done", "item": item})

    usage = response.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
    events.append(
        {
            "type": "response.completed",
            "response": {
                "id": response_id,
                "usage": {
                    "input_tokens": prompt_tokens,
                    "input_tokens_details": None,
                    "output_tokens": completion_tokens,
                    "output_tokens_details": None,
                    "total_tokens": total_tokens,
                },
            },
        }
    )
    return events


def _sse_body(events: list[dict[str, Any]]) -> bytes:
    chunks = []
    for event in events:
        event_type = event["type"]
        data = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        chunks.append(f"event: {event_type}\ndata: {data}\n\n")
    return "".join(chunks).encode("utf-8")


def _trace(event: dict[str, Any]) -> None:
    raw_path = os.environ.get("CODEX_PROXY_TRACE")
    if not raw_path:
        return
    path = Path(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _deepseek_request(payload: dict[str, Any], authorization: str | None) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    auth = authorization or (f"Bearer {api_key}" if api_key else None)
    headers = {"content-type": "application/json", "accept": "application/json"}
    if auth:
        headers["authorization"] = auth
    request = Request(DEEPSEEK_CHAT_URL, data=body, headers=headers, method="POST")
    max_retries = max(0, int(os.environ.get("CODEX_PROXY_MAX_RETRIES", "2")))
    timeout = max(1, int(os.environ.get("CODEX_PROXY_UPSTREAM_TIMEOUT", "120")))
    retryable_statuses = {408, 429, 500, 502, 503, 504}
    for attempt in range(max_retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code not in retryable_statuses or attempt >= max_retries:
                raise
        except (URLError, TimeoutError, IncompleteRead, json.JSONDecodeError):
            if attempt >= max_retries:
                raise
        delay = min(2**attempt, 4)
        _trace({"phase": "upstream_retry", "attempt": attempt + 1, "delay_seconds": delay})
        time.sleep(delay)
    raise RuntimeError("unreachable DeepSeek retry state")


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json")

    def do_GET(self) -> None:
        if self.path not in {"/v1/models", "/models"}:
            self.send_error(404, "unsupported path")
            return
        model = os.environ.get("LLM_MODEL_NAME", "deepseek-v4-pro")
        self._send_json(200, {"object": "list", "data": [{"id": model, "object": "model"}]})

    def do_POST(self) -> None:
        is_chat = self.path in {"/v1/chat/completions", "/chat/completions"}
        is_responses = self.path in {"/v1/responses", "/responses"}
        if not is_chat and not is_responses:
            self.send_error(404, "unsupported path")
            return
        if "zstd" in self.headers.get("content-encoding", "").lower():
            self._send_json(
                415,
                {"error": {"message": "Set enable_request_compression=false for this adapter."}},
            )
            return

        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as exc:
            self._send_json(400, {"error": {"message": f"invalid json: {exc}"}})
            return

        started = time.time()
        _trace(
            {
                "path": self.path,
                "phase": "request",
                "incoming_authorization": bool(self.headers.get("authorization")),
                "environment_api_key": bool(
                    os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
                ),
            }
        )
        try:
            if is_chat:
                if isinstance(payload.get("messages"), list):
                    payload["messages"] = normalize_messages(payload["messages"])
                response = _deepseek_request(payload, self.headers.get("authorization"))
                self._send_json(200, response)
                _trace(
                    {
                        "path": self.path,
                        "status": 200,
                        "elapsed_seconds": round(time.time() - started, 3),
                        "usage": response.get("usage"),
                    }
                )
                return

            translated, tool_metadata = responses_to_chat(payload)
            response = _deepseek_request(translated, self.headers.get("authorization"))
            events = chat_response_to_events(response, tool_metadata)
            body = _sse_body(events)
            self._send(200, body, "text/event-stream")
            _trace(
                {
                    "path": self.path,
                    "status": 200,
                    "elapsed_seconds": round(time.time() - started, 3),
                    "input_items": len(payload.get("input") or []),
                    "tools": len(translated.get("tools") or []),
                    "usage": response.get("usage"),
                }
            )
        except HTTPError as exc:
            response_body = exc.read()
            self._send(exc.code, response_body, exc.headers.get("content-type", "application/json"))
            _trace(
                {
                    "path": self.path,
                    "status": exc.code,
                    "elapsed_seconds": round(time.time() - started, 3),
                    "upstream_error_bytes": len(response_body),
                }
            )
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            self._send_json(502, {"error": {"message": f"DeepSeek upstream error: {exc}"}})
            _trace(
                {
                    "path": self.path,
                    "status": 502,
                    "elapsed_seconds": round(time.time() - started, 3),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )


def main() -> None:
    port = int(os.environ.get("CODEX_DEEPSEEK_PROXY_PORT", "18787"))
    host = os.environ.get("CODEX_DEEPSEEK_PROXY_HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), ProxyHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
