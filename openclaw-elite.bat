@echo off
:: OpenClaw Elite Launcher - Windows Batch Wrapper
:: This batch file provides easy access to the PowerShell launcher

cd /d "%~dp0"

if "%1"=="" goto :menu
if /i "%1"=="verify" goto :verify
if /i "%1"=="diag" goto :diagnostics
if /i "%1"=="vision" goto :visioncheck
if /i "%1"=="status" goto :status
if /i "%1"=="config" goto :config
if /i "%1"=="fix" goto :fix
if /i "%1"=="interactive" goto :interactive
if /i "%1"=="fast" goto :fast
if /i "%1"=="power" goto :power
if /i "%1"=="help" goto :help

:menu
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     🦞 OpenClaw Elite Dev Environment                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo  [1] Launch Copilot CLI (default model)
echo  [2] Launch with FAST model (gpt-4o-mini)
echo  [3] Launch with POWER model (claude-sonnet-4)
echo  [4] Interactive Menu
echo  [5] Run Diagnostics
echo  [6] Quick Status Check
echo  [7] Show Configuration
echo  [8] Verify OpenClaw API
echo  [9] Check Vision Backend
echo  [E] Elite Tools Menu
echo  [P] Phone Control 📱
echo  [M] Memory & Self-Awareness 🧠
echo  [F] Fix Config Issues
echo  [Q] Quick Launch (skip checks)
echo  [H] Help
echo  [X] Quit
echo.
set /p choice="Select option: "

if "%choice%"=="1" goto :default
if "%choice%"=="2" goto :fast
if "%choice%"=="3" goto :power
if "%choice%"=="4" goto :interactive
if "%choice%"=="5" goto :diagnostics
if "%choice%"=="6" goto :status
if "%choice%"=="7" goto :config
if "%choice%"=="8" goto :verify
if "%choice%"=="9" goto :visioncheck
if /i "%choice%"=="e" goto :elite
if /i "%choice%"=="p" goto :phone
if /i "%choice%"=="m" goto :memory
if /i "%choice%"=="f" goto :fix
if /i "%choice%"=="q" goto :quick
if /i "%choice%"=="h" goto :help
if /i "%choice%"=="x" exit /b 0
goto :menu

:default
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1"
goto :end

:fast
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Model fast
goto :end

:power
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Model power
goto :end

:interactive
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Interactive
goto :end

:verify
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Verify
goto :end

:diagnostics
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Diagnostics
goto :end

:visioncheck
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -VisionCheck
goto :end

:elite
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Interactive
goto :end

:phone
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite-phone.ps1" -Interactive
goto :end

:memory
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite-memory.ps1" -Interactive
goto :end

:status
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Status
goto :end

:config
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Config
goto :end

:fix
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Fix
goto :end

:quick
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Quick
goto :end

:help
powershell -ExecutionPolicy Bypass -File "%~dp0openclaw-elite.ps1" -Help
goto :end

:end
echo.
pause
