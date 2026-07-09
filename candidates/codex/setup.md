# codex setup

This candidate uses a pinned local Codex CLI runtime:

- Package: `@openai/codex@0.81.0`
- Install command: `npm install --prefix candidates/codex/runtime081 @openai/codex@0.81.0 --ignore-scripts --save-exact`
- Command: `candidates/codex/runtime081/node_modules/.bin/codex.cmd`
- Verified version: `codex-cli 0.81.0`
- Candidate config: `candidates/codex/config.toml`
- Workdir: `candidates/codex/workdir`
- Workdir instructions: `candidates/codex/workdir/AGENTS.md`

The runner executes Codex in non-interactive mode:

```powershell
codex exec --json --disable shell_tool --cd candidates/codex/workdir --skip-git-repo-check --sandbox read-only <prompt>
```

The candidate config defines a DeepSeek OpenAI-compatible provider:

- `model_provider=deepseek`
- `base_url=https://api.deepseek.com/v1`
- `model=deepseek-v4-pro`
- `env_key=LLM_API_KEY`
- `wire_api=chat`

The runner sets `CODEX_HOME=candidates/codex` so the benchmark uses this
candidate-scoped `config.toml`. It also maps the shell's `LLM_API_KEY` to the
process environment without writing secrets to disk.

For DeepSeek compatibility, the runner starts
`candidates/codex/deepseek_chat_proxy.py` on `127.0.0.1:18788` and overrides the
Codex provider base URL to that local `/v1` endpoint. The proxy forwards to
DeepSeek's chat-completions endpoint and only rewrites Codex's `developer`
message role to `system`, which DeepSeek accepts.

Newer Codex CLI versions such as `0.142.5` require `wire_api=responses`.
DeepSeek's OpenAI-compatible endpoint currently returns 404 for
`/v1/responses`, so this benchmark pins a chat-completions-capable Codex CLI.

Codex's shell tool is disabled through the CLI feature flag and candidate
config, its sandbox is read-only, and approvals are disabled for the benchmark.
This leaves MCP as the intended task interface. The GATE2 canaries verify that
shell/write probes do not mutate the benchmark workspace.

`AGENTS.md` in the candidate workdir contains only benchmark role/output
instructions. It does not contain task answers or policy facts; those must still
come from the MCP tools.

`--output-schema` is intentionally not used for this candidate because this
chat-completions Codex path rejects structured output schemas.
