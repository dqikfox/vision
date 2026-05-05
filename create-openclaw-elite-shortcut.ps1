# Creates a desktop shortcut for OpenClaw Elite Launcher
# Run this script to add a convenient desktop shortcut

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\OpenClaw Elite.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$PSScriptRoot\openclaw-elite.ps1`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Description = "OpenClaw Elite Dev Environment"
$Shortcut.Save()

Write-Host "✓ Desktop shortcut created: OpenClaw Elite.lnk" -ForegroundColor Green
Write-Host "  Target: $PSScriptRoot\openclaw-elite.ps1" -ForegroundColor DarkGray
