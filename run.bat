@echo off
echo ========================================
echo   Face Recognition System - Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating...
    python -m venv venv
    echo [SUCCESS] Virtual environment created!
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
echo [INFO] Checking dependencies...
echo [INFO] Installing/Updating dependencies...
pip install -r requirements.txt
echo [SUCCESS] Dependencies checked!

REM Start the server
echo ========================================
echo   Starting Face Recognition System
echo ========================================
echo.
echo [INFO] Server will start at http://127.0.0.1:8000
echo [INFO] API Docs available at http://127.0.0.1:8000/docs
echo [INFO] Frontend: Open frontend/index.html in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

python -m app.main

pause
