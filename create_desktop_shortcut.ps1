# Create Desktop Shortcut for VISION EXECUTIVE CONSOLE

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\VISION EXECUTIVE CONSOLE.lnk")

# Correct the path to the launcher
$CurrentDir = Get-Location
$LauncherPath = "$CurrentDir\vision_master_launcher.ps1"

# Icon - target PowerShell to execute the script in minimized window
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$LauncherPath`""
$Shortcut.WorkingDirectory = "$CurrentDir"
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.IconLocation = "shell32.dll, 161" # A nice accessibility/eye icon
$Shortcut.Description = "Launch VISION Universal Accessibility Operator & Executive Dashboard"
$Shortcut.Save()

Write-Host "  [OK] VISION EXECUTIVE CONSOLE shortcut created on Desktop" -ForegroundColor Green
