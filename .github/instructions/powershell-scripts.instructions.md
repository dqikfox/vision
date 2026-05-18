---
applyTo: "**/*.ps1"
---

# Vision PowerShell Scripts Instructions

## PowerShell Standards
- Use **approved verbs**: `Get-`, `Set-`, `Start-`, `Stop-`, `Test-`, etc.
- Use PascalCase for function names: `Start-VisionBackend`
- Use camelCase for variables: `$backendProcess`
- Add comment-based help for all functions
- Use `[CmdletBinding()]` for advanced functions

## Error Handling
Always use `try/catch` with `ErrorAction`:
```powershell
try {
    $result = Invoke-WebRequest -Uri $url -ErrorAction Stop
} catch {
    Write-Error "Failed to connect: $_"
    return $false
}
```

Set `$ErrorActionPreference = "Stop"` at script start for strict error handling.

## Vision-Specific Patterns

### Port Checking
Before starting services, check if ports are already in use:
```powershell
function Test-PortInUse {
    param([int]$Port)

    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $connection
}

if (Test-PortInUse 8765) {
    Write-Host "Vision backend already running on port 8765" -ForegroundColor Green
    return
}
```

### Process Management
When starting background processes:
```powershell
$processParams = @{
    FilePath = "python"
    ArgumentList = "live_chat_app.py"
    NoNewWindow = $true
    PassThru = $true
}
$process = Start-Process @processParams

# Store PID for cleanup
$global:VisionBackendPID = $process.Id
```

### Health Check Pattern
Always verify services are actually responding:
```powershell
function Test-VisionHealth {
    param([string]$BaseUrl = "http://localhost:8765")

    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 5 -ErrorAction Stop
        return $response.status -eq "healthy"
    } catch {
        Write-Warning "Health check failed: $_"
        return $false
    }
}

# Wait for backend to be ready
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    if (Test-VisionHealth) {
        Write-Host "✓ Backend is healthy" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 1
    $attempt++
}
```

### Ollama Management
Vision launchers manage Ollama server. Follow this pattern:
```powershell
# Check if Ollama is already running
$ollamaProcess = Get-Process ollama -ErrorAction SilentlyContinue
if ($null -eq $ollamaProcess) {
    Write-Host "Starting Ollama..." -ForegroundColor Yellow

    # Read config for bind address
    $config = Get-Content "vision_command_center_config.json" | ConvertFrom-Json
    $ollamaHost = $config.ollama_access_mode

    # Start Ollama with configured settings
    $env:OLLAMA_HOST = $ollamaHost
    Start-Process "ollama" -ArgumentList "serve" -NoNewWindow

    Start-Sleep -Seconds 3
}
```

## Configuration Loading
Load Vision config from JSON:
```powershell
function Get-VisionConfig {
    $configPath = Join-Path $PSScriptRoot "vision_command_center_config.json"

    if (-not (Test-Path $configPath)) {
        Write-Error "Configuration file not found: $configPath"
        return $null
    }

    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        return $config
    } catch {
        Write-Error "Failed to parse configuration: $_"
        return $null
    }
}

$config = Get-VisionConfig
$visionHost = $config.vision_host ?? "127.0.0.1"
$visionPort = $config.vision_port ?? 8765
```

## Output Formatting
Use colored output for better UX:
```powershell
Write-Host "✓ Success message" -ForegroundColor Green
Write-Host "⚠ Warning message" -ForegroundColor Yellow
Write-Host "✗ Error message" -ForegroundColor Red
Write-Host "ℹ Info message" -ForegroundColor Cyan
```

Create visual separators:
```powershell
$separator = "─" * 60
Write-Host $separator -ForegroundColor DarkGray
Write-Host " VISION MASTER LAUNCHER" -ForegroundColor Cyan
Write-Host $separator -ForegroundColor DarkGray
```

## Browser Automation
When opening browsers:
```powershell
function Open-VisionUI {
    param([string]$Url = "http://localhost:8765")

    # Check if already open (avoid duplicate tabs)
    $chromeProcess = Get-Process chrome -ErrorAction SilentlyContinue

    if ($null -eq $chromeProcess) {
        Start-Process $Url
    } else {
        # Browser already open, just open new tab
        Start-Process $Url -WindowStyle Hidden
    }
}
```

## Cleanup and Exit
Always provide clean exit:
```powershell
function Stop-VisionStack {
    Write-Host "`nStopping Vision services..." -ForegroundColor Yellow

    # Stop backend
    if ($global:VisionBackendPID) {
        Stop-Process -Id $global:VisionBackendPID -Force -ErrorAction SilentlyContinue
        Write-Host "✓ Backend stopped" -ForegroundColor Green
    }

    # Optionally stop Ollama (if managed)
    if ($global:ManagedOllama) {
        $ollamaProcess = Get-Process ollama -ErrorAction SilentlyContinue
        if ($ollamaProcess) {
            Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue
            Write-Host "✓ Ollama stopped" -ForegroundColor Green
        }
    }
}

# Register cleanup on exit
Register-EngineEvent PowerShell.Exiting -Action { Stop-VisionStack }
```

## Parameter Validation
Use parameter attributes for better UX:
```powershell
function Start-Vision {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$false)]
        [ValidateRange(1024, 65535)]
        [int]$Port = 8765,

        [Parameter(Mandatory=$false)]
        [ValidateSet("127.0.0.1", "0.0.0.0")]
        [string]$Host = "127.0.0.1",

        [Parameter(Mandatory=$false)]
        [switch]$SkipBrowser
    )

    # Function implementation
}
```

## Script Headers
Include metadata at top of scripts:
```powershell
<#
.SYNOPSIS
    Vision Master Launcher - Starts the complete Vision stack

.DESCRIPTION
    Launches Ollama server, Vision backend, and opens the web UI.
    Performs health checks and provides status feedback.

.PARAMETER Host
    Bind address for Vision backend (default: 127.0.0.1)

.PARAMETER Port
    Port for Vision backend (default: 8765)

.EXAMPLE
    .\vision_master_launcher.ps1
    Starts Vision on localhost:8765

.EXAMPLE
    .\vision_master_launcher.ps1 -Host 0.0.0.0 -Port 9000
    Starts Vision on all interfaces, port 9000

.NOTES
    Requires: Python 3.14+, Ollama
    Author: Vision Team
    Version: 2.0
#>
```

## Environment Variables
Set environment variables for Python:
```powershell
$env:PYTHONPATH = "c:\project\vision"
$env:VISION_BASE_URL = "http://localhost:8765"
$env:OLLAMA_HOST = "http://localhost:11434"
```

## Logging
Create logs for troubleshooting:
```powershell
$logPath = Join-Path $PSScriptRoot "logs\launcher_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
New-Item -ItemType Directory -Path (Split-Path $logPath) -Force | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"

    Add-Content -Path $logPath -Value $logMessage

    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARN"  { Write-Host $logMessage -ForegroundColor Yellow }
        "INFO"  { Write-Host $logMessage -ForegroundColor Cyan }
        default { Write-Host $logMessage }
    }
}
```

## Windows-Specific
Use Windows-specific cmdlets when needed:
```powershell
# Check Windows Firewall
$firewallRule = Get-NetFirewallRule -DisplayName "Vision Backend" -ErrorAction SilentlyContinue
if ($null -eq $firewallRule) {
    Write-Host "Creating firewall rule..." -ForegroundColor Yellow
    New-NetFirewallRule -DisplayName "Vision Backend" `
                        -Direction Inbound `
                        -LocalPort 8765 `
                        -Protocol TCP `
                        -Action Allow
}
```

## Testing
Test PowerShell scripts with Pester:
```powershell
Describe "Vision Launcher Tests" {
    It "Should detect port in use" {
        Test-PortInUse 8765 | Should -BeOfType [bool]
    }

    It "Should load configuration" {
        $config = Get-VisionConfig
        $config | Should -Not -BeNullOrEmpty
        $config.vision_host | Should -Not -BeNullOrEmpty
    }
}
```
