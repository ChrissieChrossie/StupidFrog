@echo off
REM Builds dist\StupidFrog.exe: one file, no Python needed on the target PC.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -m venv .venv
".venv\Scripts\python.exe" -m pip install -e ".[build]" || goto :error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean StupidFrog.spec || goto :error
echo.
echo Fertig: dist\StupidFrog.exe
pause
exit /b 0
:error
echo Build fehlgeschlagen.
pause
exit /b 1
