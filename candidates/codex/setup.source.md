# Codex source runtime

This runtime is for the domain-enhanced evaluation round. The previous Codex
0.81 MCP-only baseline remains documented in `setup.md`.

## Locked source

- Repository: `https://github.com/openai/codex.git`
- Tag: `rust-v0.144.4`
- Tag commit: `8c68d4c87dc54d38861f5114e920c3de2efa5876`
- Rust toolchain: `1.95.0`
- Source build file: `Dockerfile.source`
- Runtime image file: `Dockerfile.runtime`

The Cargo lockfile in the source tag is inconsistent with the workspace
manifests. The source build therefore performs one dependency resolution,
saves the resolved lockfile, and immediately repeats the release build with
`--locked`. Both the upstream and resolved lockfiles are retained for audit.
Cargo registry and target directories are bind-mounted to
`candidates/codex/build-cache` so the large Rust build does not consume the
Docker system disk.

## Build

The source toolchain image is `blackbox-eval/codex-toolchain:1.95.0`. The
release build runs inside that image with these mounted paths:

- source: `/src`
- Cargo home: `/cargo-home`
- target: `/target`
- retained artifacts: `/artifacts`

After `source-artifacts/codex` is generated, build the small non-root runtime:

```powershell
docker build `
  -f candidates/codex/Dockerfile.runtime `
  -t blackbox-eval/codex-source:0.144.4 `
  candidates/codex
```

## DeepSeek protocol adapter

Codex 0.144.4 only supports `wire_api = "responses"`, while the available
DeepSeek endpoint exposes Chat Completions. The independent
`deepseek_chat_proxy.py` adapter translates:

- Responses messages and tool history to Chat Completions messages;
- function and namespaced MCP tools to DeepSeek function tools;
- DeepSeek tool calls and assistant messages to Responses SSE events;
- Codex output schemas to DeepSeek JSON mode plus an explicit schema
  instruction.

The adapter does not modify the Codex Agent Loop. Strict final field checking
remains the responsibility of the shared `submit_audit_result` tool in GATE2.
Set `NO_PROXY` and `no_proxy` for the adapter's container hostname so local
tool-loop traffic is not sent to the workstation HTTP proxy.

## DeepSeek model metadata

`model_catalog.deepseek.json` registers `deepseek-v4-pro` with the source
runtime so Codex does not silently use fallback metadata. The context window is
fixed at 131072 tokens and automatic compaction starts at 100000 tokens. The
runtime image copies the source tag's `models-manager/prompt.md` to
`/opt/codex-source/base_instructions.md`; `config.source.toml` selects that
file so adding the DeepSeek catalog does not replace Codex's native Agent
instructions. The model catalog and base-instruction hashes are recorded in
`config/source_eval_lock.yaml`.

The runtime Dockerfile uses `COPY --chmod=0755` for the compiled binary. This
keeps the executable bit without creating a second full binary layer.

## Container configuration and evidence

`config.source.toml` enables the complete tool surface inside an isolated,
non-root container and points both MCP servers at read-only benchmark inputs.
Ground Truth, historical answers, judge code, and other candidates' traces are
not mounted. Successful Canary artifacts are stored under
`runs/gate1_v2_source/codex-canary`.
