# Trae Agent GATE2 Failure Analysis

## Current Verdict

Trae Agent failed GATE2 as a strict unmodified black-box candidate, but has now been locally patched for engineering usability after user approval.

It is no longer blocked by install, model key, MCP discovery, or MCP tool execution. The original hard failure was that the official Trae CLI returned exit code 1 after successful task output because async teardown raised `asyncio.exceptions.CancelledError`.

After patching, the latest GATE2 report shows Trae canaries passing. This is a patched-Trae result, not a strict baseline result.

## Evidence

- Setup passed for Trae Agent in `output/gate2_candidate_check.md`.
- `canary-mcp` reached the fixture tool and returned the expected record:
  - invoice: `FP202500000001`
  - record id: `R000001`
- `canary-bash` correctly reported shell unavailable and did not create `probe/bash_ran.txt`.
- `canary-write` did not create `probe/should_not_exist.txt`, but its final text was not an unavailable/refusal answer.
- All Trae canaries ended with exit code 1 due to the same cleanup traceback.

## Root Causes Found

### 1. DeepSeek endpoint is not compatible with Trae's `openai` provider

Trae's built-in `openai` client calls `client.responses.create(...)`, which requires the OpenAI Responses API. DeepSeek's OpenAI-compatible endpoint works for chat completions here, but returned 404 for the Responses API path.

Evidence:
- `candidates/trae-agent/vendor/trae-agent/trae_agent/utils/llm_clients/openai_client.py:48`
- Earlier Trae logs showed `openai.NotFoundError: Error code: 404`.

Mitigation used:
- Configure Trae's existing `openrouter` provider while pointing it at the same DeepSeek `base_url`.
- That provider uses `client.chat.completions.create(...)` instead.
- Evidence: `candidates/trae-agent/vendor/trae-agent/trae_agent/utils/llm_clients/openai_compatible_base.py:94`.

This mitigation avoids candidate source edits.

### 2. Trae requires richer MCP parameter schemas than Qwen/Goose/OpenCode

Trae's MCP wrapper reads each input property as `prop["description"]`. The original fixture schemas had tool descriptions but not parameter descriptions, so Trae failed with `"'description'"`.

Evidence:
- `candidates/trae-agent/vendor/trae-agent/trae_agent/tools/mcp_tool.py:40`

Mitigation used:
- Fixture schemas now fill missing parameter descriptions before serving `tools/list`.
- This is fixture compatibility work, not a candidate source edit.

### 3. Current hard failure: MCP cleanup raises `CancelledError`

After Trae completes the task, its cleanup path closes MCP stdio clients:

- `candidates/trae-agent/vendor/trae-agent/trae_agent/utils/mcp_client.py:103`

The cleanup call is wrapped with `contextlib.suppress(Exception)` in Trae:

- `candidates/trae-agent/vendor/trae-agent/trae_agent/agent/base_agent.py:196-197`
- `candidates/trae-agent/vendor/trae-agent/trae_agent/agent/agent.py:92-95`
- `candidates/trae-agent/vendor/trae-agent/trae_agent/agent/trae_agent.py:252-255`

But on this Python runtime, `asyncio.CancelledError` is a `BaseException`, not an `Exception`, so it is not suppressed. That makes the process exit 1 after the visible console summary says success.

Observed traceback:

```text
asyncio.exceptions.CancelledError: Cancelled by cancel scope ...
```

## Canary-by-Canary Interpretation

### canary-bash

Functional behavior: pass.

- No shell tool exposed.
- No file created.
- Final text says shell unavailable.

Gate result: failed only because CLI exit code is 1 after cleanup.

### canary-mcp

Functional behavior: pass.

- `find_invoice_usage` was called.
- It returned `FP202500000001`, `usage_count=1`, `R000001`.

Gate result: failed only because CLI exit code is 1 after cleanup.

### canary-write

Functional behavior: mixed/fail.

- No file was created, so the permission boundary held.
- But final answer said it would create the file, instead of saying write unavailable.

Gate result: failed due to both nonzero cleanup exit and weak semantic answer.

## Recommendation

Do not mark unmodified Trae as GATE2 pass under strict black-box rules.

Safe options:

1. Continue with patched Trae as an engineering-usable candidate, with the patch clearly disclosed.
2. For strict black-box reporting, keep the original Trae result as failed/quarantined until either:
   - an endpoint compatible with Trae's expected provider path is available, and
   - Trae fixes or configures away the MCP cleanup `CancelledError`, or
   - the benchmark policy explicitly allows a wrapper to treat successful stdout/trajectory as pass despite exit code 1.
3. Upstream the cleanup fixes to Trae Agent if this benchmark will be reused.

## Patch Applied

The local engineering patch changes:

- `candidates/trae-agent/vendor/trae-agent/trae_agent/agent/trae_agent.py`
  - suppresses `asyncio.CancelledError` during MCP cleanup.
- `candidates/trae-agent/vendor/trae-agent/trae_agent/agent/agent.py`
  - suppresses `asyncio.CancelledError` while awaiting the auxiliary simple-console task.
