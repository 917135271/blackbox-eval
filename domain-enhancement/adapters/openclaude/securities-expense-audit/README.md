# OpenClaude Adapter

Load this adapter with OpenClaude's `--plugin-dir` option. The runner sets `AUDIT_PLUGIN_ROOT` to this directory, passes the benchmark MCP configuration explicitly, and enables non-interactive JSON or stream-JSON trace output.

Business behavior comes from the generated `skills/` and `shared/` directories. Edit the canonical shared core instead of these generated copies.
