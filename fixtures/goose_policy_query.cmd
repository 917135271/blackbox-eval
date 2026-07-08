@echo off
set "PYTHONIOENCODING=utf-8"
set "EVAL_POLICY_CORPUS_DIR=%~dp0..\..\synth-pipeline\output\corpus"
python "%~dp0policy_query_mcp.py" %*
