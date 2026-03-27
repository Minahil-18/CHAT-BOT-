@echo off
title Voice Travel Chatbot - Quick Start
color 0A

echo ========================================
echo   Voice Travel Chatbot - Quick Launch
echo ========================================
echo.
echo Starting server...
echo Open browser at: http://localhost:8000
echo.

cd /d "%~dp0phase5_voice"
start http://localhost:8000
py app_voice.py

pause
