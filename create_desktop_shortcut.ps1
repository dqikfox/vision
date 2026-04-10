# Create Desktop Shortcut for VISION ELITE

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\VISION ELITE.lnk")

# Correct the path to the launcher - $PSScriptRoot might not be available in all shells
$CurrentDir = Get-Location
$LauncherPath = "$CurrentDir\vision_elite_launcher.ps1"

# Icon - try to find a nice system icon or use PowerShell
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$LauncherPath`""
$Shortcut.WorkingDirectory = "$CurrentDir"
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.IconLocation = "shell32.dll, 161" # A nice accessibility/eye icon
$Shortcut.Description = "Launch VISION Universal Accessibility Operator"
$Shortcut.Save()

Write-Host "  [OK] VISION ELITE shortcut created on Desktop" -ForegroundColor Green
