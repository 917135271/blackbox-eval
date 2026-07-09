import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"


def normalize_messages(messages: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    skip: set[int] = set()
    for index, message in enumerate(messages):
        if index in skip:
            continue
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
                normalized.append(candidate)
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


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        if self.path not in {"/v1/chat/completions", "/chat/completions"}:
            self.send_error(404, "unsupported path")
            return

        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception as exc:
            self.send_error(400, f"invalid json: {exc}")
            return

        if isinstance(payload.get("messages"), list):
            payload["messages"] = normalize_messages(payload["messages"])

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        auth = self.headers.get("authorization")
        headers = {
            "content-type": "application/json",
            "accept": self.headers.get("accept", "application/json"),
        }
        if auth:
            headers["authorization"] = auth
        elif api_key:
            headers["authorization"] = f"Bearer {api_key}"

        request = Request(DEEPSEEK_CHAT_URL, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=300) as response:
                response_body = response.read()
                self.send_response(response.status)
                self.send_header("content-type", response.headers.get("content-type", "application/json"))
                self.send_header("content-length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
        except HTTPError as exc:
            response_body = exc.read()
            self.send_response(exc.code)
            self.send_header("content-type", exc.headers.get("content-type", "application/json"))
            self.send_header("content-length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)


def main() -> None:
    port = int(os.environ.get("CODEX_DEEPSEEK_PROXY_PORT", "18787"))
    server = ThreadingHTTPServer(("127.0.0.1", port), ProxyHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
