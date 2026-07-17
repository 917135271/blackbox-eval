# Claude Code Best source runtime

This runtime is for the domain-enhanced evaluation round. The previous
MCP-only baseline remains documented in `setup.md`.

## Locked source

- Repository: `https://github.com/claude-code-best/claude-code.git`
- Tag: `v2.8.3`
- Commit: `7680c291ee7d8aa9cb291d518273352ad32256ec`
- Build runtime: Bun `1.3.12`
- Build file: `Dockerfile.source`
- Non-root runtime wrapper: `Dockerfile.nonroot`

The v2.8.3 source tag is not directly build-complete. It references two
optional bundled Skills, an optional Claude API documentation resource, and a
vendored ripgrep directory that are absent from the tag. The source Dockerfile
adds no-op build stubs for those disabled optional features and installs the
system ripgrep binary. It also replaces the unavailable npm mirror host in
`bun.lock` with the official npm registry while preserving locked versions and
integrity hashes.

## Build

```powershell
docker build `
  -f candidates/claude-code/Dockerfile.source `
  -t blackbox-eval/ccb-source:2.8.3 `
  candidates/claude-code/vendor/claude-code

docker build `
  -f candidates/claude-code/Dockerfile.nonroot `
  -t blackbox-eval/ccb-source-nonroot:2.8.3 `
  candidates/claude-code
```

The non-root image is required because the CLI refuses
`bypassPermissions` when executed as root. The Docker container and its
read-only input mounts are the security boundary.

## DeepSeek and tools

DeepSeek is selected through the fork's OpenAI-compatible provider:

- `CLAUDE_CODE_USE_OPENAI=1`
- `OPENAI_BASE_URL=https://api.deepseek.com`
- `OPENAI_MODEL=deepseek-v4-pro`
- `OPENAI_API_KEY` is injected from `LLM_API_KEY` at process start.

The container includes Shell, Python, SQLite, git, ripgrep, workspace file
operations, Skills, plugins, agents, and MCP support. Container MCP paths are
defined in `mcp_config.container.json`. The API key is never stored in an
image, configuration file, command artifact, or trajectory.

## GATE1 evidence

The successful Canary artifacts are stored under
`runs/gate1_v2_source/claude-code-canary`. They contain the stream-json
trajectory, MCP call log, debug log, runtime probe file, and a separate
structured-output check.
