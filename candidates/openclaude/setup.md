# OpenClaude Source Setup

Status: source build, Docker build, version check, and DeepSeek non-interactive Canary passed by 2026-07-16.

## Source Lock

- Repository: `https://github.com/Gitlawb/openclaude.git`
- Version from `package.json`: `0.24.0`
- Commit: `7b9e477519f6965b19f4c0db70ae410e3586a72c`
- Node.js: `24.14.0`
- Bun: `1.3.14`
- `bun.lock` SHA-256: `836cce31e0dc30e87a65e634e830a88915d6f5238d54a2a8b30e229ba3e70cf1`
- Built CLI SHA-256: `a592103de450fbe08f4de64a2bde13ff4ce832c97ba696569f66bec6b19cecdc`

The source checkout, dependency install, and generated CLI are ignored by Git and reproduced from this lock.

## Build

```powershell
npm install --prefix candidates/openclaude/runtime bun@1.3.14
$bun = "$PWD/candidates/openclaude/runtime/node_modules/.bin/bun.cmd"
Push-Location candidates/openclaude/vendor/openclaude
& $bun install --frozen-lockfile
& $bun run build
node dist/cli.mjs --version
Pop-Location
```

## Docker Build

`candidates/openclaude/Dockerfile.source` performs a two-stage source build with Bun `1.3.14`, Node.js 22, a non-root runtime user, and the Shell/Python/SQLite tools needed by the evaluation.

Verified Docker result:

- Image: `blackbox-eval/openclaude-source:0.24.0`
- Image ID: `sha256:b6c658a0992c89e38a07bcf5e727cf87e991c36e0025f754382ed8c5f3f8cb8e`
- Image size: `494502732` bytes
- Runtime user: `node`
- Container version: `0.24.0 (OpenClaude)`
- DeepSeek Canary: passed

Build and validate OpenClaude and OpenCode together with:

```powershell
powershell -ExecutionPolicy Bypass -File runner/build_source_candidate_images.ps1
```

The script checks both image versions and runs one DeepSeek non-interactive Canary per image without persisting the API key.

## DeepSeek Runtime

The runner maps `LLM_API_KEY` to `OPENAI_API_KEY` at process launch and sets:

- `CLAUDE_CODE_USE_OPENAI=1`
- `OPENAI_BASE_URL=https://api.deepseek.com/v1`
- `OPENAI_MODEL=deepseek-v4-pro`
- `OPENCLAUDE_CONFIG_DIR` to a candidate-local isolated directory

No secret is stored in this directory. The accepted runtime command starts with:

```powershell
node candidates/openclaude/vendor/openclaude/dist/cli.mjs -p <task> --output-format stream-json --no-session-persistence
```

The enhanced group additionally loads `domain-enhancement/adapters/openclaude/securities-expense-audit` through `--plugin-dir`; the baseline group does not load that directory.

## Verified Capabilities

- Source CLI reports `0.24.0 (OpenClaude)`.
- DeepSeek non-interactive JSON execution completed successfully.
- `--plugin-dir`, `--mcp-config`, `--agents`, tool allowlists, JSON Schema output, and stream-JSON trace flags are available in the source CLI.

Official sources checked 2026-07-15:

- `https://github.com/Gitlawb/openclaude`
- `https://openclaude.gitlawb.com/docs/cli-reference/`
- `https://openclaude.gitlawb.com/docs/skills/`
