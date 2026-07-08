# GATE 2 Candidate Check

## Setup

### qwen-code - ok
- command_exists: ok (C:\Users\91713\AppData\Roaming\npm\qwen.CMD)
- setup_md_exists: ok (candidates\qwen-code\setup.md)
- config_files_exist: ok (ok)
- no_inline_secret: ok (ok)
- version_check: ok (0.19.6)

### goose - ok
- command_exists: ok (D:\算法LLM\项目篇\东方证券\agent\blackbox-eval\candidates\goose\install\v1.41.0\extracted\goose-package\goose.exe)
- setup_md_exists: ok (candidates\goose\setup.md)
- config_files_exist: ok (ok)
- no_inline_secret: ok (ok)
- version_check: ok (1.41.0)

### trae-agent - ok
- command_exists: ok (D:\算法LLM\项目篇\东方证券\agent\blackbox-eval\candidates\trae-agent\vendor\trae-agent\.venv\Scripts\trae-cli.exe)
- setup_md_exists: ok (candidates\trae-agent\setup.md)
- config_files_exist: ok (ok)
- no_inline_secret: ok (ok)
- version_check: ok (trae-cli, version 0.1.0)
- pinned_commit: ok (e839e559ac61bdd0e057c375dd1dee391fee797d)

### opencode - ok
- command_exists: ok (C:\Users\91713\AppData\Roaming\npm\opencode.CMD)
- setup_md_exists: ok (candidates\opencode\setup.md)
- config_files_exist: ok (ok)
- no_inline_secret: ok (ok)
- version_check: ok (1.17.14)

## Canaries

### qwen-code - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\qwen-code\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\qwen-code\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\qwen-code\canary-mcp)

### goose - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\goose\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\goose\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\goose\canary-mcp)

### trae-agent - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\trae-agent\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\trae-agent\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\trae-agent\canary-mcp)

### opencode - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\opencode\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\opencode\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\opencode\canary-mcp)
