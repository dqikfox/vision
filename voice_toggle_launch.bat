@echo off
title Voice Toggle — STT / TTS
color 0A
setlocal

set "ELEVENLABS_API_KEY=sk_5f2c93b54654c98e37b122c8f8bb224d47a1ebf0aca38239"
set "PATH=%PATH%;C:\ProgramData\winget\Links;%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin"

echo.
echo  ==========================================
echo   Copilot Voice Toggle
echo   F9  Hold to speak   (auto-paste + Enter)
echo   F10 Toggle TTS on/off
echo   F11 Replay last TTS
echo   ESC Quit
echo  ==========================================
echo.

python "%~dp0voice_toggle.py"

echo.
echo  [Exited. Press any key to close.]
pause >nul
