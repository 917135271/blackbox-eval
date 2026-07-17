# Evaluation run artifacts

This directory keeps the final GATE1-GATE4 task workspaces and trajectories used by the research report.

Before publication, credential-shaped strings in nine Oh My Pi trajectory files were replaced with `[REDACTED_CREDENTIAL]`. The affected paths, replacement counts, and before/after file hashes are recorded in `docs/upload_sanitization_manifest.json`. Corresponding `workspace/run_manifest.json` trajectory hashes were refreshed after redaction.

Transient retry attempts, stale development runs, framework session databases, interrupted-process WAL files, broken `artifacts/latest` links, and launcher stdout/stderr logs remain local and are excluded by `.gitignore`.
