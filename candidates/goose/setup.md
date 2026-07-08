# goose setup

Status: installed and configured for GATE 2 setup checks.

## Official Sources

- Install: https://goose-docs.ai/docs/getting-started/installation/
- CLI commands: https://goose-docs.ai/docs/guides/goose-cli-commands/
- Providers: https://goose-docs.ai/docs/getting-started/providers/
- Config files: https://goose-docs.ai/docs/guides/config-files/
- Custom extensions: https://goose-docs.ai/docs/tutorials/custom-extensions/

## Pinned Version

- Release: `v1.41.0`
- Asset: `goose-x86_64-pc-windows-msvc.zip`
- Install path: `candidates/goose/install/v1.41.0/extracted/goose-package/goose.exe`
- Verified command: `goose.exe --version`

## Runtime

- Headless command: `goose.exe run --no-session --no-profile --provider openai --model deepseek-v4-flash`
- Workdir: `candidates/goose/workdir`
- Provider: built-in `openai`
- Base URL mapping: `OPENAI_HOST=https://api.deepseek.com`
- Model mapping: `GOOSE_MODEL=deepseek-v4-flash`
- API key mapping: `OPENAI_API_KEY` is populated from `LLM_API_KEY` by the runner.

## MCP

The runner passes the fixture servers with `--with-extension` using distinct wrapper commands so Goose does not collapse both stdio servers into the same `python__*` extension namespace:

- `policy_query`: `fixtures/goose_policy_query.cmd`
- `expense_query`: `fixtures/goose_expense_query.cmd`

## Native Tool Controls

- `--no-profile` prevents loading user/default Goose extensions.
- No built-in extensions are requested.
- Only the two fixture MCP stdio extensions are added for benchmark runs.
