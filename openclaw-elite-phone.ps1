# OpenClaw Elite Phone Integration
# Full phone control via ADB for Android devices

param(
    [string]$Device = "",
    [switch]$ListDevices,
    [switch]$Screenshot,
    [string]$SavePath = "",
    [switch]$Interactive,
    [switch]$Status,
    [switch]$ConnectWiFi,
    [string]$IpAddress = "",
    [switch]$Mirror,
    [switch]$Help
)

$script:Version = "1.0.0"
$script:AdbPath = "C:\Users\CHANN0$\AppData\Local\Android\Sdk\platform-tools\adb.exe"
$script:DefaultScreenshotPath = "$env:USERPROFILE\Desktop\phone-screenshot-$(Get-Date -Format 'yyyyMMdd-HHmmss').png"

$Colors = @{
    Success = 'Green'
    Info = 'Cyan'
    Warning = 'Yellow'
    Error = 'Red'
    Accent = 'Magenta'
    Phone = 'DarkCyan'
}

function Write-Status($Message, $Type = 'Info') {
    $color = $Colors[$Type]
    $prefix = switch ($Type) {
        'Success' { '✓' }
        'Error' { '✗' }
        'Warning' { '⚠' }
        default { '→' }
    }
    Write-Host "$prefix $Message" -ForegroundColor $color
}

function Show-Banner {
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║     📱 OpenClaw Elite Phone Control v$script:Version              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $Colors.Phone
}

function Show-Help {
    @"
OpenClaw Elite Phone Control

USAGE:
    .\openclaw-elite-phone.ps1 [OPTIONS]

OPTIONS:
    -ListDevices         List all connected devices
    -Device <id>        Target specific device
    -Screenshot          Take a screenshot
    -SavePath <path>    Save screenshot to specific path
    -Interactive         Interactive phone control menu
    -Status              Show phone connection status
    -ConnectWiFi         Connect to device via WiFi ADB
    -IpAddress <ip>     IP address for WiFi connection
    -Mirror              Mirror phone screen to PC
    -Help                Show this help

EXAMPLES:
    .\openclaw-elite-phone.ps1 -ListDevices
    .\openclaw-elite-phone.ps1 -Screenshot
    .\openclaw-elite-phone.ps1 -Interactive
    .\openclaw-elite-phone.ps1 -ConnectWiFi -IpAddress 192.168.1.100
"@ | Write-Host
}

function Test-Adb {
    if (-not (Test-Path $script:AdbPath)) {
        Write-Status "ADB not found at $script:AdbPath" 'Error'
        return $false
    }
    return $true
}

function Invoke-Adb($Arguments) {
    if (-not (Test-Adb)) { return $null }
    try {
        $output = & $script:AdbPath $Arguments 2>&1
        return $output
    } catch {
        Write-Status "ADB command failed: $_" 'Error'
        return $null
    }
}

function Get-Devices {
    $output = Invoke-Adb @('devices', '-l')
    if ($output) {
        $lines = $output -split "`n" | Where-Object { $_ -match '^\S+\s+(device|unauthorized|offline)' }
        $devices = @()
        foreach ($line in $lines) {
            $parts = $line -split '\s+', 2
            if ($parts.Count -ge 2) {
                $devices += [PSCustomObject]@{
                    Serial = $parts[0]
                    Status = ($parts[1] -split '\s+')[0]
                    Details = $parts[1]
                }
            }
        }
        return $devices
    }
    return @()
}

function Show-DeviceStatus {
    Write-Host ""
    Write-Host "── Phone Connection Status ──" -ForegroundColor $Colors.Accent

    if (-not (Test-Adb)) {
        Write-Status "ADB not available" 'Error'
        return
    }

    $devices = Get-Devices
    if ($devices.Count -eq 0) {
        Write-Status "No devices connected" 'Warning'
        Write-Host ""
        Write-Host "To connect your phone:" -ForegroundColor $Colors.Info
        Write-Host "  1. Enable Developer Options on your phone" -ForegroundColor $Colors.Dim
        Write-Host "  2. Enable USB Debugging" -ForegroundColor $Colors.Dim
        Write-Host "  3. Connect via USB and accept the debugging prompt" -ForegroundColor $Colors.Dim
        Write-Host "  4. Or use: .\openclaw-elite-phone.ps1 -ConnectWiFi -IpAddress <your-phone-ip>" -ForegroundColor $Colors.Dim
    } else {
        Write-Status "Found $($devices.Count) device(s)" 'Success'
        foreach ($dev in $devices) {
            $statusColor = if ($dev.Status -eq 'device') { 'Success' } else { 'Warning' }
            Write-Status "$($dev.Serial): $($dev.Status)" $statusColor
            if ($dev.Details) {
                Write-Host "       $($dev.Details)" -ForegroundColor $Colors.Dim
            }
        }
    }
}

function Invoke-Screenshot($DeviceId = "", $OutputPath = "") {
    $path = if ($OutputPath) { $OutputPath } else { $script:DefaultScreenshotPath }

    Write-Status "Taking screenshot..." 'Info'

    $deviceArg = if ($DeviceId) { "-s", $DeviceId } else { @() }

    # Take screenshot on device
    $tempFile = "/sdcard/openclaw-screenshot.png"
    Invoke-Adb (@($deviceArg) + @('shell', 'screencap', $tempFile) | Where-Object { $_ })

    # Pull to PC
    Invoke-Adb (@($deviceArg) + @('pull', $tempFile, $path) | Where-Object { $_ })

    # Clean up
    Invoke-Adb (@($deviceArg) + @('shell', 'rm', $tempFile) | Where-Object { $_ })

    if (Test-Path $path) {
        Write-Status "Screenshot saved: $path" 'Success'
        return $path
    } else {
        Write-Status "Failed to save screenshot" 'Error'
        return $null
    }
}

function Invoke-Tap($X, $Y, $DeviceId = "") {
    $deviceArg = if ($DeviceId) { "-s", $DeviceId } else { @() }
    Invoke-Adb (@($deviceArg) + @('shell', 'input', 'tap', $X, $Y) | Where-Object { $_ })
    Write-Status "Tapped at $X, $Y" 'Success'
}

function Invoke-Swipe($X1, $Y1, $X2, $Y2, $Duration = 300, $DeviceId = "") {
    $deviceArg = if ($DeviceId) { "-s", $DeviceId } else { @() }
    Invoke-Adb (@($deviceArg) + @('shell', 'input', 'swipe', $X1, $Y1, $X2, $Y2, $Duration) | Where-Object { $_ })
    Write-Status "Swiped from ($X1, $Y1) to ($X2, $Y2)" 'Success'
}

function Send-Text($Text, $DeviceId = "") {
    $escaped = $Text -replace ' ', '%s'
    $deviceArg = if ($DeviceId) { "-s", $DeviceId } else { @() }
    Invoke-Adb (@($deviceArg) + @('shell', 'input', 'text', $escaped) | Where-Object { $_ })
    Write-Status "Text sent: $Text" 'Success'
}

function Send-KeyEvent($KeyCode, $DeviceId = "") {
    $deviceArg = if ($DeviceId) { "-s", $DeviceId } else { @() }
    Invoke-Adb (@($deviceArg) + @('shell', 'input', 'keyevent', $KeyCode) | Where-Object { $_ })
}

function Invoke-Key($KeyName, $DeviceId = "") {
    $keyCodes = @{
        'HOME' = 3
        'BACK' = 4
        'POWER' = 26
        'VOLUME_UP' = 24
        'VOLUME_DOWN' = 25
        'MENU' = 82
        'ENTER' = 66
        'ESCAPE' = 111
        'TAB' = 61
        'SPACE' = 62
    }

    if ($keyCodes.ContainsKey($KeyName.ToUpper())) {
        $code = $keyCodes[$KeyName.ToUpper()]
        Send-KeyEvent $code $DeviceId
        Write-Status "Key pressed: $KeyName" 'Success'
    } else {
        Write-Status "Unknown key: $KeyName" 'Error'
    }
}

function Start-App($PackageName, $DeviceId = "") {
    $deviceArg = if ($DeviceId) { "-s", $DeviceId } else { @() }
    Invoke-Adb (@($deviceArg) + @('shell', 'monkey', '-p', $PackageName, '-c', 'android.intent.category.LAUNCHER', '1') | Where-Object { $_ })
    Write-Status "Launched: $PackageName" 'Success'
}

function Get-InstalledApps($DeviceId = "") {
    $deviceArg = if ($DeviceId) { "-s", $DeviceId } else { @() }
    $output = Invoke-Adb (@($deviceArg) + @('shell', 'pm', 'list', 'packages', '-3') | Where-Object { $_ })
    $apps = $output | Where-Object { $_ -match '^package:' } | ForEach-Object { $_ -replace '^package:', '' }
    return $apps
}

function Connect-WiFiAdb($IpAddress) {
    Write-Status "Connecting to $IpAddress via WiFi ADB..." 'Info'

    # First ensure device is connected via USB
    $devices = Get-Devices
    $usbDevice = $devices | Where-Object { $_.Status -eq 'device' -and $_.Serial -notmatch ':' } | Select-Object -First 1

    if (-not $usbDevice) {
        Write-Status "No USB device found. Connect via USB first to enable WiFi ADB." 'Error'
        return $false
    }

    # Enable TCP/IP mode
    Invoke-Adb @('tcpip', '5555')
    Start-Sleep -Seconds 2

    # Connect via WiFi
    $result = Invoke-Adb @('connect', "$($IpAddress):5555")

    if ($result -match 'connected|already connected') {
        Write-Status "Connected to $IpAddress" 'Success'
        return $true
    } else {
        Write-Status "Failed to connect: $result" 'Error'
        return $false
    }
}

function Start-ScreenMirror {
    Write-Status "Starting screen mirror..." 'Info'

    # Check for scrcpy
    $scrcpy = Get-Command scrcpy -ErrorAction SilentlyContinue
    if (-not $scrcpy) {
        Write-Status "scrcpy not found. Install it for screen mirroring:" 'Warning'
        Write-Host "  winget install Genymobile.scrcpy" -ForegroundColor $Colors.Dim
        return
    }

    Start-Process scrcpy -ArgumentList "--turn-screen-off", "--stay-awake"
    Write-Status "Screen mirroring started" 'Success'
}

function Show-InteractiveMenu {
    $selectedDevice = ""

    while ($true) {
        Clear-Host
        Show-Banner
        Write-Host ""

        # Show current device
        $devices = Get-Devices
        if ($devices.Count -gt 0) {
            if (-not $selectedDevice) {
                $selectedDevice = $devices[0].Serial
            }
            Write-Host "  Selected Device: $selectedDevice" -ForegroundColor $Colors.Success
        } else {
            Write-Host "  No device connected" -ForegroundColor $Colors.Warning
        }

        Write-Host ""
        Write-Host "  [1] Take Screenshot" -ForegroundColor $Colors.Info
        Write-Host "  [2] Tap on Screen" -ForegroundColor $Colors.Info
        Write-Host "  [3] Swipe on Screen" -ForegroundColor $Colors.Info
        Write-Host "  [4] Type Text" -ForegroundColor $Colors.Info
        Write-Host "  [5] Press Key" -ForegroundColor $Colors.Info
        Write-Host "  [6] Launch App" -ForegroundColor $Colors.Info
        Write-Host "  [7] List Installed Apps" -ForegroundColor $Colors.Info
        Write-Host "  [8] Screen Mirror (scrcpy)" -ForegroundColor $Colors.Info
        Write-Host "  [9] Change Device" -ForegroundColor $Colors.Info
        Write-Host "  [S] Show Device Status" -ForegroundColor $Colors.Info
        Write-Host "  [W] Connect WiFi ADB" -ForegroundColor $Colors.Info
        Write-Host "  [Q] Quit" -ForegroundColor $Colors.Dim
        Write-Host ""

        $choice = Read-Host "Select option"

        switch ($choice) {
            '1' {
                $path = Invoke-Screenshot -DeviceId $selectedDevice
                if ($path) {
                    Write-Host "  Screenshot: $path" -ForegroundColor $Colors.Dim
                }
                Read-Host "Press Enter to continue"
            }
            '2' {
                $x = Read-Host "Enter X coordinate"
                $y = Read-Host "Enter Y coordinate"
                Invoke-Tap $x $y $selectedDevice
                Read-Host "Press Enter to continue"
            }
            '3' {
                $x1 = Read-Host "Enter start X"
                $y1 = Read-Host "Enter start Y"
                $x2 = Read-Host "Enter end X"
                $y2 = Read-Host "Enter end Y"
                $duration = Read-Host "Enter duration in ms (default: 300)"
                if (-not $duration) { $duration = 300 }
                Invoke-Swipe $x1 $y1 $x2 $y2 $duration $selectedDevice
                Read-Host "Press Enter to continue"
            }
            '4' {
                $text = Read-Host "Enter text to type"
                Send-Text $text $selectedDevice
                Read-Host "Press Enter to continue"
            }
            '5' {
                Write-Host "Available keys: HOME, BACK, POWER, VOLUME_UP, VOLUME_DOWN, MENU, ENTER" -ForegroundColor $Colors.Dim
                $key = Read-Host "Enter key name"
                Invoke-Key $key $selectedDevice
                Read-Host "Press Enter to continue"
            }
            '6' {
                $package = Read-Host "Enter package name (e.g., com.whatsapp)"
                Start-App $package $selectedDevice
                Read-Host "Press Enter to continue"
            }
            '7' {
                Write-Status "Fetching installed apps..." 'Info'
                $apps = Get-InstalledApps $selectedDevice
                $apps | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor $Colors.Dim }
                if ($apps.Count -gt 20) {
                    Write-Host "  ... and $($apps.Count - 20) more" -ForegroundColor $Colors.Dim
                }
                Read-Host "Press Enter to continue"
            }
            '8' {
                Start-ScreenMirror
                Read-Host "Press Enter to continue"
            }
            '9' {
                $devices = Get-Devices
                if ($devices.Count -gt 1) {
                    Write-Host "Available devices:" -ForegroundColor $Colors.Info
                    for ($i = 0; $i -lt $devices.Count; $i++) {
                        Write-Host "  [$i] $($devices[$i].Serial) ($($devices[$i].Status))" -ForegroundColor $Colors.Dim
                    }
                    $selection = Read-Host "Select device number"
                    if ($selection -match '^\d+$' -and [int]$selection -lt $devices.Count) {
                        $selectedDevice = $devices[[int]$selection].Serial
                    }
                } else {
                    Write-Status "Only one device connected" 'Warning'
                }
                Read-Host "Press Enter to continue"
            }
            's' { Show-DeviceStatus; Read-Host "Press Enter to continue" }
            'S' { Show-DeviceStatus; Read-Host "Press Enter to continue" }
            'w' {
                $ip = Read-Host "Enter phone IP address"
                Connect-WiFiAdb $ip
                Read-Host "Press Enter to continue"
            }
            'W' {
                $ip = Read-Host "Enter phone IP address"
                Connect-WiFiAdb $ip
                Read-Host "Press Enter to continue"
            }
            'q' { return }
            'Q' { return }
        }
    }
}

# ── Main Entry Point ─────────────────────────────────────────────────────────
if ($Help) {
    Show-Help
    exit 0
}

Show-Banner

if ($ListDevices) {
    Show-DeviceStatus
    exit 0
}

if ($Status) {
    Show-DeviceStatus
    exit 0
}

if ($Screenshot) {
    Invoke-Screenshot -DeviceId $Device -OutputPath $SavePath
    exit 0
}

if ($ConnectWiFi -and $IpAddress) {
    Connect-WiFiAdb $IpAddress
    exit 0
}

if ($Mirror) {
    Start-ScreenMirror
    exit 0
}

if ($Interactive) {
    Show-InteractiveMenu
    exit 0
}

# Default: show status
Show-DeviceStatus
Write-Host ""
Write-Host "Use -Interactive for full phone control menu" -ForegroundColor $Colors.Info
Write-Host "Use -Help for all options" -ForegroundColor $Colors.Dim
