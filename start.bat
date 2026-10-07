@echo off
REM Starts the desktop frog with a double click.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m frog
) else (
    set PYTHONPATH=%~dp0src
    python -m frog
)
if errorlevel 1 pause
