@echo off
REM Run the Python GUI game from the correct directory
cd /d "%~dp0"
python -B main_gui.py
if %errorlevel% neq 0 (
    echo.
    echo There was an error running the game. If you see 'python' is not recognized, make sure Python is in your PATH.
)
pause
