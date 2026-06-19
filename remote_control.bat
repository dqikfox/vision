@echo off
:: Claude Remote Control launcher
:: Temporarily removes apiKeyHelper from settings to allow claude.ai OAuth
:: Restores settings on exit

setlocal

set ANTHROPIC_BASE_URL=
set ANTHROPIC_API_KEY=

set SETTINGS=C:\Users\CHANN0$\.claude\settings.json
set BACKUP=C:\Users\CHANN0$\.claude\settings.json.bak

:: Backup and patch settings (remove apiKeyHelper)
powershell -NoProfile -Command ^
  "$s = Get-Content '%SETTINGS%' -Raw | ConvertFrom-Json; ^
   Copy-Item '%SETTINGS%' '%BACKUP%' -Force; ^
   $s.PSObject.Properties.Remove('apiKeyHelper'); ^
   if ($s.env) { $s.env.PSObject.Properties.Remove('ANTHROPIC_BASE_URL') }; ^
   $s | ConvertTo-Json -Depth 10 | Set-Content '%SETTINGS%' -Encoding UTF8; ^
   Write-Host 'Auth patched - using claude.ai OAuth'"

cd /d C:\project\vision

:: Run Remote Control (blocking)
claude remote-control %*

:: Restore original settings
copy /Y "%BACKUP%" "%SETTINGS%" >nul
echo Settings restored.