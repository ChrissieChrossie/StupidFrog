@echo off
REM Starts the desktop frog with a double click.
cd /d "%~dp0"
REM Finds the code even if "pip install -e ." has not been run yet.
set PYTHONPATH=%~dp0src
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m frog
) else (
    python -m frog
)
if errorlevel 1 pause
