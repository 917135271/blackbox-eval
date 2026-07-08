@echo off
set "PYTHONIOENCODING=utf-8"
set "EVAL_EXPENSE_DB=%~dp0..\..\synth-pipeline\output\data\expense.db"
python "%~dp0expense_query_mcp.py" %*
