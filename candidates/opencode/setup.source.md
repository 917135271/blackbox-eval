# OpenCode Expanded Evaluation Source Lock

Status: Windows source build, Docker source-runtime build, version check, and DeepSeek non-interactive Canary passed by 2026-07-16.

## Source Lock

- Repository: `https://github.com/anomalyco/opencode.git`
- Version from `packages/opencode/package.json`: `1.18.1`
- Commit: `04bdf7732bae0cbb2ab3e003d65bddb8d56edacf`
- Required package manager: `bun@1.3.14`
- `bun.lock` SHA-256: `7f0bf1846b4a2f9b004d80ecc84db366ba9941ed76015d2f779d0be7a1662894`

The globally installed `opencode 1.17.14` belongs to the earlier 55-task baseline. It must not be used as the formal runtime for the expanded evaluation unless the source lock is deliberately changed and recorded.

## Resolved Windows Source Build

The original checkout path contains Chinese characters and is long enough for Bun and `node-gyp` to fail while linking `tree-sitter-powershell`. A junction and `SUBST` drive are not sufficient because Bun resolves them to the original path. The reproducible Windows build therefore uses a local, no-network clone of the locked commit in an ASCII-only short build directory.

The `tree-sitter-bash` and `tree-sitter-powershell` packages are consumed through their WASM files in `packages/opencode/src/tool/shell.ts`; OpenCode does not import their native Node bindings. Dependency lifecycle scripts are skipped during this build, while both required WASM files are checked before compilation.

Verified source result:

- Build directory commit: `04bdf7732bae0cbb2ab3e003d65bddb8d56edacf`
- Build directory `bun.lock` SHA-256: `7f0bf1846b4a2f9b004d80ecc84db366ba9941ed76015d2f779d0be7a1662894`
- Source binary version: `1.18.1`
- Source binary SHA-256: `cdf39ec3df50c7ae2517caf2238d520c9aa4dd7832117f1651d393291b90abbe`
- Source binary size: `142476800` bytes
- DeepSeek JSON Canary: passed, final answer `OK`, exit code `0`

The source binary is copied to ignored runtime path `candidates/opencode/runtime/opencode.exe`. The old global `1.17.14` binary is not used.

## Docker Build

`Dockerfile.source` applies the same safe dependency rule and runs as a non-root user. Its default `source-runtime` target executes the locked source directly with Bun and injects version `1.18.1`. This is the formal engineering runtime because the optional single-binary packaging stage consumed more than one hour and made Docker Desktop's WSL backend unresponsive.

The strict compiled runtime remains available as target `binary-runtime` for offline investigation, but it is not required for GATE3 or GATE4. Framework source, dependency lock, model configuration, Skills, MCP, permissions, and task behavior are identical between the two targets; only the CLI delivery form differs.

Verified Docker result:

- Image: `blackbox-eval/opencode-source:1.18.1`
- Image ID: `sha256:1b7769c4144ff4bb8b21f2f84bbd88a40c91e5375ec81ef15432a0445977a5bb`
- Image size: `2693888260` bytes
- Runtime user: `agent`
- Container version: `1.18.1`
- DeepSeek Canary: passed

Reproduction entry:

```powershell
docker build --progress=plain `
  -f candidates/opencode/Dockerfile.source `
  -t blackbox-eval/opencode-source:1.18.1 `
  candidates/opencode/vendor/opencode
```

Optional strict binary build:

```powershell
docker build --progress=plain --target binary-runtime `
  -f candidates/opencode/Dockerfile.source `
  -t blackbox-eval/opencode-binary-source:1.18.1 `
  candidates/opencode/vendor/opencode
```

After Docker is healthy, build and validate both new candidates with:

```powershell
powershell -ExecutionPolicy Bypass -File runner/build_source_candidate_images.ps1
```

## Expanded Runtime Contract

- Non-interactive entry: `opencode run`
- Provider: DeepSeek through the frozen OpenAI-compatible configuration
- Skills: generated adapter `skills/` copied to isolated `.opencode/skills/`
- Subagents: `.opencode/agents/`
- MCP: policy query, expense query, and enhanced-group audit control
- Trace: JSON events plus task-local MCP and workspace artifacts

Official sources checked 2026-07-15:

- `https://github.com/anomalyco/opencode`
- `https://opencode.ai/docs/cli/`
- `https://opencode.ai/docs/skills/`
- `https://opencode.ai/docs/agents/`
