@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 -m venv .venv
) else (
  python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
  echo Python 3.10 or newer is needed. Install Python with its launcher and try again.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Installation failed. Copy the error above and send it to Aizen's project chat.
  pause
  exit /b 1
)
echo Setup complete. Double-click RUN_GAME.bat to play.
pause
