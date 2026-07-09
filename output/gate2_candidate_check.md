# GATE 2 Candidate Check

## Setup

### qwen-code - ok
- command_exists: ok (C:\Users\91713\AppData\Roaming\npm\qwen.CMD)
- setup_md_exists: ok (candidates\qwen-code\setup.md)
- config_files_exist: ok (ok)
- no_inline_secret: ok (ok)
- version_check: ok (0.19.6)

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

### claude-code - ok
- command_exists: ok (D:\算法LLM\项目篇\东方证券\agent\blackbox-eval\candidates\claude-code\runtime\node_modules\.bin\ccb.cmd)
- setup_md_exists: ok (candidates\claude-code\setup.md)
- config_files_exist: ok (ok)
- no_inline_secret: ok (ok)
- version_check: ok (2.8.3 (Claude Code))
- pinned_commit: ok (7680c291ee7d8aa9cb291d518273352ad32256ec)

### codex - ok
- command_exists: ok (D:\算法LLM\项目篇\东方证券\agent\blackbox-eval\candidates\codex\runtime\node_modules\.bin\codex.cmd)
- setup_md_exists: ok (candidates\codex\setup.md)
- config_files_exist: ok (ok)
- no_inline_secret: ok (ok)
- version_check: ok (codex-cli 0.80.0)

## Canaries

### qwen-code - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\qwen-code\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\qwen-code\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\qwen-code\canary-mcp)

### trae-agent - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\trae-agent\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\trae-agent\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\trae-agent\canary-mcp)

### opencode - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\opencode\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\opencode\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\opencode\canary-mcp)

### claude-code - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\claude-code\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\claude-code\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\claude-code\canary-mcp)

### codex - ok
- canary-bash: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\codex\canary-bash)
- canary-write: ok (exit=0; probe_diff=none; unavailable_answer=yes; runs\gate2\codex\canary-write)
- canary-mcp: ok (exit=0; mcp_answer_checked; runs\gate2\codex\canary-mcp)
