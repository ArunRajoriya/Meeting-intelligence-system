@echo off
REM Meeting Intelligence System - Startup Script (Windows)

echo ==================================
echo Meeting Intelligence System
echo ==================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo WARNING: Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
if not exist "venv\Scripts\uvicorn.exe" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Dependencies installed
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Creating template .env file...
    (
        echo GROQ_API_KEY=your_groq_api_key_here
        echo.
        echo # Optional transcription providers ^(uncomment and add key^)
        echo # OPENAI_API_KEY=your_openai_key_here
        echo # ASSEMBLYAI_API_KEY=your_assemblyai_key_here
    ) > .env
    echo Template .env created. Please add your API keys!
    echo.
    echo Get your Groq API key from: https://console.groq.com/keys
    echo.
    pause
    exit /b 1
)

REM Create meeting_notes directory if it doesn't exist
if not exist "meeting_notes\" (
    mkdir meeting_notes
    echo Created meeting_notes directory
)

REM Start the server
echo.
echo Starting server...
echo ==================================
echo.
echo Server will be available at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
