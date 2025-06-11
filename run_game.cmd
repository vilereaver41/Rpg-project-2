@echo off
echo Python Game Launcher
echo =================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in your PATH.
    echo Please install Python and make sure it's added to your PATH.
    pause
    exit /b 1
)

REM Run the main game from the current directory
echo Starting the game...
echo.
python -B main.py

REM If there was an error, display a message
if %errorlevel% neq 0 (
    echo.
    echo There was an error running the game. 
    echo If you see 'python' is not recognized, make sure Python is in your PATH.
)

echo.
echo Game closed.
pause