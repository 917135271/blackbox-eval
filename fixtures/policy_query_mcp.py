from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"


def log_path() -> Path | None:
    raw = os.environ.get("EVAL_TASK_LOG")
    if not raw:
        return None
    path = Path(raw)
    if path.suffix:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    path.mkdir(parents=True, exist_ok=True)
    return path / "tool_calls.jsonl"


def write_log(tool_name: str, arguments: dict[str, Any], result: Any, error: str | None = None) -> None:
    path = log_path()
    if path is None:
        return
    event = {
        "ts": time.time(),
        "server": "policy_query_mcp",
        "tool": tool_name,
        "arguments": arguments,
        "ok": error is None,
        "error": error,
        "result_preview": result if error else preview(result),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def preview(value: Any) -> Any:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(text) <= 1200:
        return value
    return {"preview": text[:1200], "truncated": True}


def corpus_dir() -> Path:
    path = Path(os.environ.get("EVAL_POLICY_CORPUS_DIR", str(DEFAULT_CORPUS_DIR)))
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_documents() -> list[dict[str, str]]:
    docs = []
    for path in sorted(corpus_dir().glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
        docs.append({"doc_id": path.name, "title": title, "text": text})
    return docs


def tokenize(text: str) -> list[str]:
    terms = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())
    return terms


def snippets(text: str, query: str, max_snippets: int = 3, width: int = 90) -> list[str]:
    terms = [term for term in tokenize(query) if len(term.strip()) > 0]
    if not terms:
        return [text[:width]]
    hits: list[tuple[int, str]] = []
    for line in text.splitlines():
        score = sum(line.lower().count(term) for term in terms)
        if score:
            hits.append((score, line.strip()))
    hits.sort(key=lambda item: item[0], reverse=True)
    if not hits:
        return [text[:width]]
    return [line[:width] for _, line in hits[:max_snippets]]


def list_policy_docs() -> dict[str, Any]:
    """List available policy documents with document id and title."""
    return {
        "corpus_dir": str(corpus_dir()),
        "documents": [{"doc_id": doc["doc_id"], "title": doc["title"]} for doc in load_documents()],
    }


def search_policy(query: str, top_k: int = 5) -> dict[str, Any]:
    """Search policy corpus with simple in-memory BM25 and return ranked snippets."""
    docs = load_documents()
    top_k = max(1, min(int(top_k), 10))
    tokenized = [tokenize(doc["text"]) for doc in docs]
    doc_freq: Counter[str] = Counter()
    for terms in tokenized:
        doc_freq.update(set(terms))
    avg_len = sum(len(terms) for terms in tokenized) / max(1, len(tokenized))
    query_terms = tokenize(query)
    scores = []
    for doc, terms in zip(docs, tokenized):
        counts = Counter(terms)
        score = 0.0
        for term in query_terms:
            if not counts[term]:
                continue
            idf = math.log((len(docs) - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5) + 1)
            denom = counts[term] + 1.5 * (1 - 0.75 + 0.75 * len(terms) / max(1, avg_len))
            score += idf * counts[term] * 2.5 / denom
        if score > 0:
            scores.append(
                {
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "score": round(score, 4),
                    "snippets": snippets(doc["text"], query),
                }
            )
    scores.sort(key=lambda item: item["score"], reverse=True)
    return {"query": query, "top_k": top_k, "results": scores[:top_k]}


def get_policy_doc(doc_id: str) -> dict[str, Any]:
    """Return a full policy document by doc_id."""
    for doc in load_documents():
        if doc["doc_id"] == doc_id:
            return {"doc_id": doc["doc_id"], "title": doc["title"], "text": doc["text"]}
    return {"doc_id": doc_id, "found": False, "text": ""}


def get_policy_excerpt(doc_id: str, query: str, max_chars: int = 1200) -> dict[str, Any]:
    """Return policy excerpts from one document that are relevant to a query."""
    doc = get_policy_doc(doc_id)
    max_chars = max(200, min(int(max_chars), 4000))
    if not doc.get("text"):
        return {"doc_id": doc_id, "found": False, "excerpts": []}
    found = snippets(doc["text"], query, max_snippets=6, width=max_chars)
    return {"doc_id": doc_id, "title": doc["title"], "query": query, "excerpts": found}


TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "list_policy_docs": list_policy_docs,
    "search_policy": search_policy,
    "get_policy_doc": get_policy_doc,
    "get_policy_excerpt": get_policy_excerpt,
}


TOOL_SCHEMAS = [
    {
        "name": "list_policy_docs",
        "description": list_policy_docs.__doc__,
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "search_policy",
        "description": search_policy.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_policy_doc",
        "description": get_policy_doc.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {"doc_id": {"type": "string"}},
            "required": ["doc_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_policy_excerpt",
        "description": get_policy_excerpt.__doc__,
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string"},
                "query": {"type": "string"},
                "max_chars": {"type": "integer", "minimum": 200, "maximum": 4000, "default": 1200},
            },
            "required": ["doc_id", "query"],
            "additionalProperties": False,
        },
    },
]


def ensure_tool_schema_descriptions() -> None:
    for tool in TOOL_SCHEMAS:
        tool["description"] = tool.get("description") or f"Call {tool['name']}."
        properties = tool.get("inputSchema", {}).get("properties", {})
        for param_name, param_schema in properties.items():
            param_schema.setdefault("description", f"{param_name} parameter for {tool['name']}.")


ensure_tool_schema_descriptions()


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    arguments = arguments or {}
    try:
        result = TOOLS[name](**arguments)
        write_log(name, arguments, result)
        return result
    except Exception as exc:
        write_log(name, arguments, None, error=str(exc))
        raise


def handle_rpc(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "policy_query_mcp", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": TOOL_SCHEMAS}
        elif method == "tools/call":
            params = request.get("params", {})
            result_obj = call_tool(params["name"], params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(result_obj, ensure_ascii=False)}], "isError": False}
        elif method == "notifications/initialized":
            return None
        else:
            raise ValueError(f"unsupported method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}


def serve_stdio() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        response = handle_rpc(json.loads(line))
        if response is not None:
            print(json.dumps(response, ensure_ascii=True), flush=True)


def self_test() -> dict[str, Any]:
    docs = call_tool("list_policy_docs")
    search = call_tool("search_policy", {"query": "部门总经理 审批 10000", "top_k": 3})
    doc_id = search["results"][0]["doc_id"] if search["results"] else docs["documents"][0]["doc_id"]
    full = call_tool("get_policy_doc", {"doc_id": doc_id})
    excerpt = call_tool("get_policy_excerpt", {"doc_id": doc_id, "query": "审批 金额", "max_chars": 500})
    return {
        "list_policy_docs": {"count": len(docs["documents"]), "first": docs["documents"][0]},
        "search_policy": search,
        "get_policy_doc": {"doc_id": full["doc_id"], "title": full["title"], "chars": len(full["text"])},
        "get_policy_excerpt": excerpt,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=False, indent=2))
    else:
        serve_stdio()


if __name__ == "__main__":
    main()
