#!/usr/bin/env pwsh
# VISION - Universal Accessibility Operator launcher
#
# Startup flow:
# 1. Validate Python + required packages.
# 2. Start Ollama automatically when it is required and not already listening.
# 3. Start the FastAPI / WebSocket backend when it is not already listening.
# 4. Confirm health + doctor endpoints before opening the UI surfaces.

param(
    [switch]$Reload,
    [switch]$Debug,
    [switch]$NoOllama,
    [switch]$NoBrowser
)

$ErrorActionPreference = "SilentlyContinue"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$PYTHON = if ($pythonCommand) { $pythonCommand.Source } else { "python" }
$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
$OLLAMA = if ($ollamaCommand) { $ollamaCommand.Source } else { $null }
$APP_DIR = $PSScriptRoot
$APP_FILE = Join-Path $APP_DIR "live_chat_app.py"
$CONFIG_FILE = Join-Path $APP_DIR "vision_command_center_config.json"
$LOG_FILE = Join-Path $APP_DIR "vision_launch.log"
$ERR_FILE = Join-Path $APP_DIR "vision_error.log"
$UI_URL = "http://localhost:8765"
$COMMAND_CENTER_URL = "$UI_URL/command-center"
$HEALTH_URL = "$UI_URL/api/health"
$DOCTOR_URL = "$UI_URL/api/command-center/doctor"

function ok($msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function err($msg) { Write-Host "  [ERR] $msg" -ForegroundColor Red }
function hdr($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function dot($msg) { Write-Host "  [..] $msg" -ForegroundColor DarkGray }

function Get-LauncherConfig {
    $default = @{
        open_primary_ui = $true
        open_command_center = $false
        prefer_app_window = $true
        ollama_access_mode = "local"
        ollama_host = "127.0.0.1:11434"
        ollama_origins = "http://localhost:8765,http://127.0.0.1:8765"
        ollama_models_path = "F:\\models"
    }
    if (-not (Test-Path $CONFIG_FILE)) {
        return $default
    }
    try {
        $raw = Get-Content $CONFIG_FILE -Raw | ConvertFrom-Json
        if ($null -eq $raw.launcher) {
            return $default
        }
        return @{
            open_primary_ui = if ($null -ne $raw.launcher.open_primary_ui) { [bool]$raw.launcher.open_primary_ui } else { $default.open_primary_ui }
            open_command_center = if ($null -ne $raw.launcher.open_command_center) { [bool]$raw.launcher.open_command_center } else { $default.open_command_center }
            prefer_app_window = if ($null -ne $raw.launcher.prefer_app_window) { [bool]$raw.launcher.prefer_app_window } else { $default.prefer_app_window }
            ollama_access_mode = if ($null -ne $raw.launcher.ollama_access_mode -and "$($raw.launcher.ollama_access_mode)".Trim()) { "$($raw.launcher.ollama_access_mode)".Trim().ToLowerInvariant() } else { $default.ollama_access_mode }
            ollama_host = if ($null -ne $raw.launcher.ollama_host -and "$($raw.launcher.ollama_host)".Trim()) { "$($raw.launcher.ollama_host)".Trim() } else { $default.ollama_host }
            ollama_origins = if ($null -ne $raw.launcher.ollama_origins -and "$($raw.launcher.ollama_origins)".Trim()) { "$($raw.launcher.ollama_origins)".Trim() } else { $default.ollama_origins }
            ollama_models_path = if ($null -ne $raw.launcher.ollama_models_path -and "$($raw.launcher.ollama_models_path)".Trim()) { "$($raw.launcher.ollama_models_path)".Trim() } else { $default.ollama_models_path }
        }
    } catch {
        warn "Could not parse vision_command_center_config.json; using launcher defaults"
        return $default
    }
}

function Open-PreferredBrowser([string]$Url, [bool]$PreferAppWindow) {
    $browsers = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
    )
    if ($PreferAppWindow) {
        foreach ($browser in $browsers) {
            if (Test-Path $browser) {
                Start-Process $browser -ArgumentList "--app=$Url --window-size=1400,900"
                ok "Opened in: $(Split-Path $browser -Leaf)"
                return
            }
        }
    }
    Start-Process $Url
    ok "Opened in default browser"
}

function Wait-ForPort([int]$Port, [int]$TimeoutSeconds) {
    for ($i = 0; $i -lt $TimeoutSeconds; $i++) {
        Start-Sleep -Seconds 1
        if (netstat -ano | Select-String ":$Port.*LISTENING") {
            return $true
        }
    }
    return $false
}

function Get-LanBaseUrls([int]$Port) {
    $addresses = @()
    try {
        $addresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop | Where-Object {
            $_.IPAddress -and
            $_.IPAddress -notlike "127.*" -and
            $_.IPAddress -notlike "169.254.*"
        } | Select-Object -ExpandProperty IPAddress -Unique
    } catch {
        try {
            $addresses = [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() |
                Where-Object { $_.OperationalStatus -eq "Up" } |
                ForEach-Object { $_.GetIPProperties().UnicastAddresses } |
                Where-Object {
                    $_.Address.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and
                    $_.Address.IPAddressToString -notlike "127.*" -and
                    $_.Address.IPAddressToString -notlike "169.254.*"
                } |
                ForEach-Object { $_.Address.IPAddressToString } |
                Select-Object -Unique
        } catch {
            $addresses = @()
        }
    }
    return @($addresses | Sort-Object | ForEach-Object { "http://$($_):$Port" })
}

function Get-TailscaleBaseUrls([int]$Port) {
    try {
        $status = & tailscale status --json 2>$null | ConvertFrom-Json
    } catch {
        return @()
    }

    if ($null -eq $status -or $null -eq $status.Self) {
        return @()
    }

    $urls = @()
    $dnsName = "$($status.Self.DNSName)".Trim().TrimEnd(".")
    if ($dnsName) {
        $urls += "http://${dnsName}:$Port"
    }
    foreach ($ip in @($status.Self.TailscaleIPs)) {
        $ipText = "$ip".Trim()
        if ($ipText -and $ipText -match "^\d{1,3}(\.\d{1,3}){3}$") {
            $urls += "http://${ipText}:$Port"
        }
    }
    return @($urls | Select-Object -Unique)
}

function Stop-OllamaProcesses {
    $targets = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -eq 'ollama.exe' -or $_.Name -eq 'ollama app.exe') -and $_.ExecutablePath -like '*\\Ollama\\*'
    }
    foreach ($target in $targets) {
        try {
            Stop-Process -Id $target.ProcessId -Force -ErrorAction Stop
            dot "Stopped Ollama PID $($target.ProcessId)"
        } catch {
        }
    }
}

Clear-Host
Write-Host ""
Write-Host "  VISION - Universal Accessibility Operator" -ForegroundColor Cyan
if ($Reload) {
    Write-Host "  DEV MODE - hot-reload enabled" -ForegroundColor Yellow
}
Write-Host "  ----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

$startTime = Get-Date
$launcherConfig = Get-LauncherConfig
$openPrimaryUi = (-not $NoBrowser) -and $launcherConfig.open_primary_ui
$openCommandCenter = (-not $NoBrowser) -and $launcherConfig.open_command_center

hdr "STEP 1 - Python Runtime"
$pyVer = & $PYTHON --version 2>&1
if ($LASTEXITCODE -eq 0 -or $pyVer -match "Python") {
    ok "Python found: $pyVer"
} else {
    err "Python not found in PATH"
    exit 1
}

hdr "STEP 2 - Python Packages"
$packages = @(
    @{ name = "fastapi"; import = "fastapi" },
    @{ name = "uvicorn"; import = "uvicorn" },
    @{ name = "httpx"; import = "httpx" },
    @{ name = "psutil"; import = "psutil" },
    @{ name = "playwright"; import = "playwright" },
    @{ name = "pytesseract"; import = "pytesseract" },
    @{ name = "pyautogui"; import = "pyautogui" }
)
$missing = @()
foreach ($pkg in $packages) {
    $result = & $PYTHON -c "import $($pkg.import); print('OK')" 2>&1
    if ($result -eq "OK") {
        dot "$($pkg.name) loaded"
    } else {
        warn "$($pkg.name) not found"
        $missing += $pkg.name
    }
}
if ($missing.Count -gt 0) {
    warn "Missing packages: $($missing -join ', ')"
    warn "Run: pip install -r requirements.txt"
} else {
    ok "All required packages present"
}

if (-not $NoOllama) {
    # Ollama is the local model service used by Vision. If it is not already
    # listening on the standard port, start `ollama serve` automatically so
    # local-model features can come online without manual intervention.
    hdr "STEP 3 - Ollama"
    $ollamaAccessMode = if ("$($launcherConfig.ollama_access_mode)" -eq "lan") { "lan" } else { "local" }
    $defaultOllamaHost = if ($ollamaAccessMode -eq "lan") { "0.0.0.0:11434" } else { "127.0.0.1:11434" }
    $ollamaHost = if ("$($launcherConfig.ollama_host)".Trim()) { "$($launcherConfig.ollama_host)".Trim() } else { $defaultOllamaHost }
    $ollamaOrigins = if ("$($launcherConfig.ollama_origins)".Trim()) { "$($launcherConfig.ollama_origins)".Trim() } else { "http://localhost:8765,http://127.0.0.1:8765" }
    $ollamaModelsPath = if ("$($launcherConfig.ollama_models_path)".Trim()) { "$($launcherConfig.ollama_models_path)".Trim() } else { "F:\\models" }
    $env:OLLAMA_HOST = $ollamaHost
    $env:OLLAMA_ORIGINS = $ollamaOrigins
    if ($ollamaAccessMode -eq "lan") {
        warn "Ollama launcher mode: LAN exposed (host=$env:OLLAMA_HOST, origins=$env:OLLAMA_ORIGINS)"
    } else {
        ok "Ollama launcher mode: local only (host=$env:OLLAMA_HOST)"
    }
    $env:OLLAMA_MODELS = $ollamaModelsPath
    if (-not (Test-Path $ollamaModelsPath)) {
        warn "Configured Ollama models path not found: $ollamaModelsPath"
    } else {
        ok "Ollama models path: $ollamaModelsPath"
    }
    if ($OLLAMA) {
        dot "Restarting managed Ollama serve with configured model library..."
        Stop-OllamaProcesses
        Start-Sleep -Seconds 2
        Start-Process -FilePath $OLLAMA -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        if (netstat -ano | Select-String ":11434.*LISTENING") {
            ok "Ollama started"
        } else {
            warn "Ollama may still be starting"
        }
    } else {
        warn "Ollama not found on PATH"
    }
}

hdr "STEP 4 - VISION App Server"
# The backend hosts both the operator UI and the command-center APIs. Start it
# only when port 8765 is not already in use so repeated launches stay safe.
if (netstat -ano | Select-String ":8765.*LISTENING") {
    ok "VISION server already running"
} else {
    if (-not (Test-Path $APP_FILE)) {
        err "App file not found: $APP_FILE"
        exit 1
    }
    dot "Starting VISION server..."
    $uvicornArgs = @(
        "-m", "uvicorn",
        "live_chat_app:app",
        "--host", "0.0.0.0",
        "--port", "8765",
        "--log-level", "warning"
    )
    if ($Reload) {
        $uvicornArgs += "--reload"
        $uvicornArgs += "--reload-dir"
        $uvicornArgs += $APP_DIR
    }

    $startInfo = @{
        FilePath = $PYTHON
        ArgumentList = $uvicornArgs
        WorkingDirectory = $APP_DIR
        RedirectStandardOutput = $LOG_FILE
        RedirectStandardError = $ERR_FILE
    }
    if (-not $Debug) {
        $startInfo.WindowStyle = "Hidden"
    }
    Start-Process @startInfo
    dot "Waiting for server to come online..."
    if (Wait-ForPort -Port 8765 -TimeoutSeconds 35) {
        ok "VISION server started"
    } else {
        err "VISION server failed to start within timeout"
        err "Check: $ERR_FILE"
        exit 1
    }
}

hdr "STEP 5 - Health Check"
# The health and doctor checks are the success indicators for the launcher. They
# confirm the runtime is responsive before the browser UI is opened.
Start-Sleep -Seconds 1
try {
    $health = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 8
    ok "API responding"
    $statusMap = @{
        ollama = "Ollama"
        elevenlabs = "ElevenLabs"
        browser = "Playwright Browser"
        gpu = "GPU"
        ocr = "OCR"
    }
    foreach ($key in $statusMap.Keys) {
        $val = $health.$key
        if ($val -eq $true -or $val -eq "true") {
            ok "$($statusMap[$key]) online"
        } elseif ($val -eq $false -or $val -eq "false") {
            warn "$($statusMap[$key]) offline"
        } else {
            dot "$($statusMap[$key]) => $val"
        }
    }
} catch {
    warn "Health check failed: $($_.Exception.Message)"
}

try {
    $doctor = Invoke-RestMethod -Uri $DOCTOR_URL -TimeoutSec 8
    if ($doctor.ok) {
        ok "Vision Doctor reports healthy"
    } else {
        warn "Vision Doctor found issues"
        foreach ($item in $doctor.recommendations) {
            warn "Doctor: $item"
        }
    }
} catch {
    dot "Doctor endpoint not available"
}

hdr "STEP 6 - Launch UI"
$elapsed = [Math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
Write-Host ""
Write-Host "  ===============================================" -ForegroundColor DarkCyan
Write-Host "  VISION is ready  |  Startup: ${elapsed}s" -ForegroundColor Cyan
Write-Host "  ===============================================" -ForegroundColor DarkCyan
Write-Host ""

if ($openPrimaryUi) {
    Open-PreferredBrowser -Url $UI_URL -PreferAppWindow ([bool]$launcherConfig.prefer_app_window)
}
if ($openCommandCenter) {
    Start-Process $COMMAND_CENTER_URL
    ok "Opened Command Center"
}
if ($NoBrowser) {
    dot "Browser launch skipped by -NoBrowser"
}

Write-Host ""
Write-Host "  Logs:   $LOG_FILE" -ForegroundColor DarkGray
Write-Host "  Errors: $ERR_FILE" -ForegroundColor DarkGray
Write-Host "  Config: $CONFIG_FILE" -ForegroundColor DarkGray
$lanUrls = Get-LanBaseUrls -Port 8765
if ($lanUrls.Count -gt 0) {
    Write-Host "  LAN:" -ForegroundColor DarkGray
    foreach ($baseUrl in $lanUrls) {
        Write-Host "    UI:      $baseUrl" -ForegroundColor DarkGray
        Write-Host "    Control: $baseUrl/command-center" -ForegroundColor DarkGray
    }
}
$tailscaleUrls = Get-TailscaleBaseUrls -Port 8765
if ($tailscaleUrls.Count -gt 0) {
    Write-Host "  Tailscale:" -ForegroundColor DarkGray
    foreach ($baseUrl in $tailscaleUrls) {
        Write-Host "    UI:      $baseUrl" -ForegroundColor DarkGray
        Write-Host "    Control: $baseUrl/command-center" -ForegroundColor DarkGray
    }
}
Write-Host ""
