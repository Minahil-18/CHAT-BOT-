@echo off
title Voice Travel Chatbot - Startup
color 0A

echo ========================================
echo   Voice Travel Chatbot Launcher
echo ========================================
echo.

REM Change to the project directory
cd /d "%~dp0phase5_voice"

echo [1/3] Checking Ollama...
REM Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo   ✓ Ollama is already running
) else (
    echo   ! Ollama not detected. Starting Ollama...
    start "Ollama Server" ollama serve
    timeout /t 3 /nobreak > nul
    echo   ✓ Ollama started
)

echo.
echo [2/3] Starting Voice Chatbot Server...
echo   Navigate to: http://localhost:8000
echo   Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

REM Start the Python server
py app_voice.py

REM If server stops, wait for user
pause
