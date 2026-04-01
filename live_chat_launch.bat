@echo off
title Operator ? Universal Accessibility System
cd /d C:\Users\msiul\.copilot

:: Load keys from .env (one KEY=VALUE per line, # = comment)
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /v "^#" .env`) do (
    if not "%%A"=="" if not "%%B"=="" set "%%A=%%B"
)

:: Verify required key
if "%ELEVENLABS_API_KEY%"=="" (
    echo ERROR: ELEVENLABS_API_KEY not set in .env
    pause
    exit /b 1
)

python live_chat_app.py
pause
