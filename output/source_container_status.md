# OpenCode and OpenClaude Build Status

Updated: 2026-07-16 11:22 +08:00

## Final Result

OpenCode and OpenClaude have both completed source image construction, container version checks, and DeepSeek `deepseek-v4-pro` non-interactive Canaries. The shared command is:

```powershell
powershell -ExecutionPolicy Bypass -File runner/build_source_candidate_images.ps1
```

The command completed with exit code `0` and reported `OpenCode and OpenClaude image builds, versions, and DeepSeek canaries passed.` No API key is stored in an image, Dockerfile, configuration file, or trajectory.

## OpenCode

- Source commit: `04bdf7732bae0cbb2ab3e003d65bddb8d56edacf`
- Version: `1.18.1`
- Image: `blackbox-eval/opencode-source:1.18.1`
- Image ID: `sha256:1b7769c4144ff4bb8b21f2f84bbd88a40c91e5375ec81ef15432a0445977a5bb`
- Image size: `2693888260` bytes
- Runtime user: `agent`
- Runtime mode: locked source executed by Bun
- Container version check: passed, `1.18.1`
- DeepSeek Canary: passed

The original strict Linux single-binary target installed all locked dependencies but did not complete Bun packaging within one hour and made Docker Desktop's WSL backend unresponsive. It remains available as optional target `binary-runtime`, but it is excluded from the formal evaluation runtime. The default source-runtime uses the same source commit, `bun.lock`, Skills, MCP configuration, permissions, and model settings.

## OpenClaude

- Source commit: `7b9e477519f6965b19f4c0db70ae410e3586a72c`
- Version: `0.24.0`
- Image: `blackbox-eval/openclaude-source:0.24.0`
- Image ID: `sha256:b6c658a0992c89e38a07bcf5e727cf87e991c36e0025f754382ed8c5f3f8cb8e`
- Image size: `494502732` bytes
- Runtime user: `node`
- Container version check: passed, `0.24.0 (OpenClaude)`
- DeepSeek Canary: passed

## Next Gate

The container environment blocker is closed. OpenCode and OpenClaude can now enter the 12-case GATE3 baseline/enhanced development run. Formal GATE4 remains blocked until those four development groups pass and their configurations are frozen.
