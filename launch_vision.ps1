#!/usr/bin/env pwsh
# ════════════════════════════════════════════════════════════════
#  VISION — Universal Accessibility Operator  |  Launcher v2.0
#  Starts all required services, validates connections, opens UI
#  --reload flag: auto-restarts server on code changes
# ════════════════════════════════════════════════════════════════

param(
    [switch]$Reload,        # Enable uvicorn --reload (dev mode)
    [switch]$Debug,         # Show verbose server output
    [switch]$NoOllama,      # Skip Ollama startup
    [switch]$NoBrowser      # Skip opening browser UI
)

$ErrorActionPreference = 'SilentlyContinue'

# ── Paths ────────────────────────────────────────────────────────
$PYTHON   = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $PYTHON) { $PYTHON = "python" }
$OLLAMA   = (Get-Command ollama -ErrorAction SilentlyContinue)?.Source
$APP_DIR  = $PSScriptRoot
$APP_FILE = "$APP_DIR\live_chat_app.py"
$LOG_FILE = "$APP_DIR\vision_launch.log"
$UI_URL   = "http://localhost:8765"
$HEALTH   = "$UI_URL/api/health"

# ── Colors ───────────────────────────────────────────────────────
function ok($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function err($msg)  { Write-Host "  ✗ $msg" -ForegroundColor Red }
function hdr($msg)  { Write-Host "`n◆ $msg" -ForegroundColor Cyan }
function dot($msg)  { Write-Host "  · $msg" -ForegroundColor DarkGray }

Clear-Host
Write-Host ""
Write-Host "  ██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗" -ForegroundColor Blue
Write-Host "  ██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║" -ForegroundColor Blue
Write-Host "  ██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║" -ForegroundColor DarkBlue
Write-Host "  ╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║" -ForegroundColor DarkBlue
Write-Host "   ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║" -ForegroundColor DarkCyan
Write-Host "    ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  Universal Accessibility Operator — Launch Sequence" -ForegroundColor DarkGray
if ($Reload) {
    Write-Host "  ◈ DEV MODE — hot-reload enabled (uvicorn --reload)" -ForegroundColor Yellow
}
Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

$startTime = Get-Date

# ════════════════════════════════════════════════════════════════
#  STEP 1: Validate Python
# ════════════════════════════════════════════════════════════════
hdr "STEP 1 — Python Runtime"
$pyVer = & $PYTHON --version 2>&1
if ($LASTEXITCODE -eq 0 -or $pyVer -match "Python") {
    ok "Python found: $pyVer"
} else {
    err "Python not found in PATH"
    err "Cannot start VISION without Python. Aborting."
    Read-Host "`nPress Enter to exit"
    exit 1
}

# ════════════════════════════════════════════════════════════════
#  STEP 2: Check required Python packages
# ════════════════════════════════════════════════════════════════
hdr "STEP 2 — Python Packages"
$packages = @(
    @{ name='fastapi';     import='fastapi' },
    @{ name='uvicorn';     import='uvicorn' },
    @{ name='elevenlabs';  import='elevenlabs' },
    @{ name='pyttsx3';     import='pyttsx3' },
    @{ name='sounddevice'; import='sounddevice' },
    @{ name='pytesseract'; import='pytesseract' },
    @{ name='pyautogui';   import='pyautogui' },
    @{ name='psutil';      import='psutil' },
    @{ name='PIL';         import='PIL' },
    @{ name='playwright';  import='playwright' },
    @{ name='ddgs';        import='ddgs' },
    @{ name='markdownify'; import='markdownify' }
)
$missing = @()
foreach ($pkg in $packages) {
    $result = & $PYTHON -c "import $($pkg.import); print('OK')" 2>&1
    if ($result -eq 'OK') {
        dot "$($pkg.name) ✓"
    } else {
        warn "$($pkg.name) — NOT FOUND"
        $missing += $pkg.name
    }
}
if ($missing.Count -gt 0) {
    warn "Missing packages: $($missing -join ', ')"
    warn "Run: pip install -r requirements.txt"
} else {
    ok "All packages present"
}

# ════════════════════════════════════════════════════════════════
#  STEP 3: Ollama
# ════════════════════════════════════════════════════════════════
if (-not $NoOllama) {
    hdr "STEP 3 — Ollama (Local AI)"
    $ollamaRunning = netstat -ano | Select-String ':11434.*LISTENING'
    if ($ollamaRunning) {
        $pid11434 = (netstat -ano | Select-String ':11434.*LISTENING' | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -First 1)
        ok "Ollama already running (PID $pid11434)"
    } elseif ($OLLAMA) {
        dot "Starting Ollama serve…"
        Start-Process -FilePath $OLLAMA -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        ok "Ollama started"
    } else {
        warn "Ollama not found — local models unavailable"
    }

    $ollamaModels = @()
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
        $ollamaModels = $resp.models | ForEach-Object { $_.name }
        if ($ollamaModels.Count -gt 0) {
            ok "$($ollamaModels.Count) models: $($ollamaModels -join ', ')"
        } else {
            warn "No models. Run: ollama pull llama3.1:8b"
        }
    } catch { warn "Could not query Ollama models" }
}

# ════════════════════════════════════════════════════════════════
#  STEP 4: VISION App Server
# ════════════════════════════════════════════════════════════════
hdr "STEP 4 — VISION App Server (port 8765)"
$visionRunning = netstat -ano | Select-String ':8765.*LISTENING'
if ($visionRunning) {
    $pid8765 = (netstat -ano | Select-String ':8765.*LISTENING' | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -First 1)
    ok "VISION server already running (PID $pid8765)"
} else {
    dot "Starting VISION server…"
    if (-not (Test-Path $APP_FILE)) {
        err "App file not found: $APP_FILE"
        Read-Host "`nPress Enter to exit"
        exit 1
    }

    # Build uvicorn args
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
        FilePath         = $PYTHON
        ArgumentList     = $uvicornArgs
        WorkingDirectory = $APP_DIR
    }
    if ($Debug) {
        $startInfo.RedirectStandardOutput = $LOG_FILE
        $startInfo.RedirectStandardError  = "$APP_DIR\vision_error.log"
    } else {
        $startInfo.WindowStyle = "Hidden"
        $startInfo.RedirectStandardOutput = $LOG_FILE
        $startInfo.RedirectStandardError  = "$APP_DIR\vision_error.log"
    }
    Start-Process @startInfo

    dot "Waiting for server to come online…"
    $timeout = 35
    $started = $false
    for ($i = 0; $i -lt $timeout; $i++) {
        Start-Sleep -Seconds 1
        $check = netstat -ano | Select-String ':8765.*LISTENING'
        if ($check) { $started = $true; break }
        Write-Host "  · Waiting… ($($i+1)s)" -ForegroundColor DarkGray -NoNewline
        Write-Host "`r" -NoNewline
    }
    if ($started) {
        ok "VISION server started"
    } else {
        err "VISION server failed to start within ${timeout}s"
        err "Check: $APP_DIR\vision_error.log"
        notepad "$APP_DIR\vision_error.log"
        Read-Host "`nPress Enter to exit"
        exit 1
    }
}

# ════════════════════════════════════════════════════════════════
#  STEP 5: Health Check & Validation
# ════════════════════════════════════════════════════════════════
hdr "STEP 5 — Health Check"
Start-Sleep -Seconds 1
try {
    $health = Invoke-RestMethod -Uri $HEALTH -TimeoutSec 8
    ok "API responding"
    $statusMap = @{
        ollama      = 'Ollama'
        elevenlabs  = 'ElevenLabs'
        browser     = 'Playwright Browser'
        gpu         = 'GPU'
        ocr         = 'OCR (Tesseract)'
    }
    foreach ($key in $statusMap.Keys) {
        $val = $health.$key
        if ($val -eq $true -or $val -eq 'true') { ok "$($statusMap[$key])" }
        elseif ($val -eq $false -or $val -eq 'false') { warn "$($statusMap[$key]) — offline" }
        else { dot "$($statusMap[$key]) — $val" }
    }
} catch {
    warn "Health check failed: $($_.Exception.Message)"
}

# Metrics
try {
    $m = Invoke-RestMethod -Uri "$UI_URL/api/metrics" -TimeoutSec 5
    ok "Metrics: CPU=$([Math]::Round($m.cpu))% RAM=$([Math]::Round($m.ram))% DISK=$([Math]::Round($m.disk))%"
} catch { dot "Metrics not available" }

# ════════════════════════════════════════════════════════════════
#  STEP 6: Launch Browser
# ════════════════════════════════════════════════════════════════
hdr "STEP 6 — Launch UI"
$elapsed = [Math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
Write-Host ""
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkCyan
Write-Host "  VISION is ready  |  Startup: ${elapsed}s  |  $UI_URL" -ForegroundColor Cyan
if ($Reload) {
    Write-Host "  ◈ Hot-reload active — save live_chat_app.py to auto-restart" -ForegroundColor Yellow
}
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkCyan
Write-Host ""

if (-not $NoBrowser) {
    $browsers = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
    )
    $launched = $false
    foreach ($browser in $browsers) {
        if (Test-Path $browser) {
            Start-Process $browser -ArgumentList "--app=$UI_URL --window-size=1400,900"
            ok "Opened in: $(Split-Path $browser -Leaf)"
            $launched = $true
            break
        }
    }
    if (-not $launched) { Start-Process $UI_URL; ok "Opened in default browser" }
}

Write-Host ""
Write-Host "  Logs:   $LOG_FILE" -ForegroundColor DarkGray
Write-Host "  Errors: $APP_DIR\vision_error.log" -ForegroundColor DarkGray
Write-Host "  Usage:  .\launch_vision.ps1 -Reload    # hot-reload dev mode" -ForegroundColor DarkGray
Write-Host "  Usage:  .\launch_vision.ps1 -NoBrowser # no auto browser" -ForegroundColor DarkGray
Write-Host "  Press Ctrl+C to exit this window (server keeps running)" -ForegroundColor DarkGray
Write-Host ""

Start-Sleep -Seconds 4


# ── Colors ───────────────────────────────────────────────────────
function ok($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function err($msg)  { Write-Host "  ✗ $msg" -ForegroundColor Red }
function hdr($msg)  { Write-Host "`n◆ $msg" -ForegroundColor Cyan }
function dot($msg)  { Write-Host "  · $msg" -ForegroundColor DarkGray }

Clear-Host
Write-Host ""
Write-Host "  ██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗" -ForegroundColor Blue
Write-Host "  ██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║" -ForegroundColor Blue
Write-Host "  ██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║" -ForegroundColor DarkBlue
Write-Host "  ╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║" -ForegroundColor DarkBlue
Write-Host "   ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║" -ForegroundColor DarkCyan
Write-Host "    ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  Universal Accessibility Operator — Launch Sequence" -ForegroundColor DarkGray
Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

$startTime = Get-Date

# ════════════════════════════════════════════════════════════════
#  STEP 1: Validate Python
# ════════════════════════════════════════════════════════════════
hdr "STEP 1 — Python Runtime"
if (Test-Path $PYTHON) {
    $pyVer = & $PYTHON --version 2>&1
    ok "Python found: $pyVer"
} else {
    err "Python not found at: $PYTHON"
    err "Cannot start VISION without Python. Aborting."
    Read-Host "`nPress Enter to exit"
    exit 1
}

# ════════════════════════════════════════════════════════════════
#  STEP 2: Check required Python packages
# ════════════════════════════════════════════════════════════════
hdr "STEP 2 — Python Packages"
$packages = @(
    @{ name='fastapi';     import='fastapi' },
    @{ name='uvicorn';     import='uvicorn' },
    @{ name='elevenlabs';  import='elevenlabs' },
    @{ name='pyttsx3';     import='pyttsx3' },
    @{ name='sounddevice'; import='sounddevice' },
    @{ name='mss';         import='mss' },
    @{ name='pytesseract'; import='pytesseract' },
    @{ name='pyautogui';   import='pyautogui' },
    @{ name='psutil';      import='psutil' },
    @{ name='PIL';         import='PIL' },
    @{ name='playwright';  import='playwright' }
)
$missing = @()
foreach ($pkg in $packages) {
    $result = & $PYTHON -c "import $($pkg.import); print('OK')" 2>&1
    if ($result -eq 'OK') {
        dot "$($pkg.name) ✓"
    } else {
        warn "$($pkg.name) — NOT FOUND"
        $missing += $pkg.name
    }
}
if ($missing.Count -gt 0) {
    warn "Missing packages: $($missing -join ', ')"
    warn "Some features may be unavailable."
} else {
    ok "All packages present"
}

# ════════════════════════════════════════════════════════════════
#  STEP 3: Ollama
# ════════════════════════════════════════════════════════════════
hdr "STEP 3 — Ollama (Local AI)"
$ollamaRunning = netstat -ano | Select-String ':11434.*LISTENING'
if ($ollamaRunning) {
    $pid11434 = (netstat -ano | Select-String ':11434.*LISTENING' | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -First 1)
    ok "Ollama already running (PID $pid11434)"
} elseif (Test-Path $OLLAMA) {
    dot "Starting Ollama serve…"
    Start-Process -FilePath $OLLAMA -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    $ollamaRunning = netstat -ano | Select-String ':11434.*LISTENING'
    if ($ollamaRunning) {
        ok "Ollama started successfully"
    } else {
        warn "Ollama may still be starting (takes a few seconds)"
    }
} else {
    warn "Ollama not found at: $OLLAMA"
    warn "Local AI models will be unavailable"
}

# Check which models are available
$ollamaModels = @()
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
    $ollamaModels = $resp.models | ForEach-Object { $_.name }
    if ($ollamaModels.Count -gt 0) {
        ok "$($ollamaModels.Count) models available: $($ollamaModels -join ', ')"
    } else {
        warn "No models found. Run: ollama pull llama3.1:8b"
    }
} catch {
    warn "Could not query Ollama models (may still be starting)"
}

# ════════════════════════════════════════════════════════════════
#  STEP 4: VISION App Server
# ════════════════════════════════════════════════════════════════
hdr "STEP 4 — VISION App Server (port 8765)"
$visionRunning = netstat -ano | Select-String ':8765.*LISTENING'
if ($visionRunning) {
    $pid8765 = (netstat -ano | Select-String ':8765.*LISTENING' | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -First 1)
    ok "VISION server already running (PID $pid8765)"
} else {
    dot "Starting VISION server…"
    if (-not (Test-Path $APP_FILE)) {
        err "App file not found: $APP_FILE"
        Read-Host "`nPress Enter to exit"
        exit 1
    }
    $logStream = [System.IO.File]::CreateText($LOG_FILE)
    $logStream.Close()
    Start-Process -FilePath $PYTHON -ArgumentList $APP_FILE `
        -WorkingDirectory $APP_DIR `
        -RedirectStandardOutput $LOG_FILE `
        -RedirectStandardError "$APP_DIR\vision_error.log" `
        -WindowStyle Hidden
    
    dot "Waiting for server to come online…"
    $timeout = 30
    $started = $false
    for ($i = 0; $i -lt $timeout; $i++) {
        Start-Sleep -Seconds 1
        $check = netstat -ano | Select-String ':8765.*LISTENING'
        if ($check) {
            $started = $true
            break
        }
        Write-Host "  · Waiting… ($($i+1)s)" -ForegroundColor DarkGray -NoNewline
        Write-Host "`r" -NoNewline
    }
    if ($started) {
        ok "VISION server started"
    } else {
        err "VISION server failed to start within ${timeout}s"
        err "Check log: $LOG_FILE"
        warn "Attempting to open log…"
        notepad "$APP_DIR\vision_error.log"
        Read-Host "`nPress Enter to exit"
        exit 1
    }
}

# ════════════════════════════════════════════════════════════════
#  STEP 5: Health Check & Validation
# ════════════════════════════════════════════════════════════════
hdr "STEP 5 — Health Check & Model Setup"
Start-Sleep -Seconds 1  # brief settle time
try {
    $health = Invoke-RestMethod -Uri $HEALTH -TimeoutSec 8
    ok "API responding"
    
    $statusMap = @{
        ollama      = 'Ollama'
        elevenlabs  = 'ElevenLabs'
        browser     = 'Playwright Browser'
        gpu         = 'GPU'
        ocr         = 'OCR (Tesseract)'
    }
    foreach ($key in $statusMap.Keys) {
        $val = $health.$key
        if ($val -eq $true -or $val -eq 'true') {
            ok "$($statusMap[$key])"
        } elseif ($val -eq $false -or $val -eq 'false') {
            warn "$($statusMap[$key]) — offline"
        } else {
            dot "$($statusMap[$key]) — $val"
        }
    }
} catch {
    warn "Health check request failed: $($_.Exception.Message)"
    warn "Server may still be initializing"
}

# Check metrics endpoint
try {
    $metrics = Invoke-RestMethod -Uri "$UI_URL/api/metrics" -TimeoutSec 5
    ok "Metrics: CPU=$([Math]::Round($metrics.cpu))% RAM=$([Math]::Round($metrics.ram))% DISK=$([Math]::Round($metrics.disk))%"
} catch {
    dot "Metrics endpoint not available"
}

# Check voices endpoint
try {
    $voices = Invoke-RestMethod -Uri "$UI_URL/api/voices" -TimeoutSec 5
    $vCount = ($voices.voices | Measure-Object).Count
    ok "Voices: $vCount available"
    $voices.voices | ForEach-Object { dot "  · $($_.name) [$($_.type)]" }
} catch {
    dot "Voices endpoint not available"
}

# Set preferred model: qwen3-coder:480b-cloud (cloud-hosted via Ollama)
$DEFAULT_MODEL    = "qwen3-coder:480b-cloud"
$DEFAULT_PROVIDER = "ollama"
try {
    $modelAvail = $ollamaModels | Where-Object { $_ -like "*qwen3-coder*480b*" }
    if ($modelAvail) {
        $body = "{`"provider`":`"$DEFAULT_PROVIDER`",`"model`":`"$DEFAULT_MODEL`"}"
        Invoke-RestMethod -Uri "$UI_URL/api/model" -Method POST -ContentType "application/json" -Body $body | Out-Null
        ok "Active model: $DEFAULT_PROVIDER / $DEFAULT_MODEL"
    } else {
        warn "qwen3-coder:480b-cloud not found in Ollama — using default model"
    }
} catch {
    dot "Could not set active model"
}

# ════════════════════════════════════════════════════════════════
#  STEP 6: Launch Browser
# ════════════════════════════════════════════════════════════════
hdr "STEP 6 — Launch UI"
$elapsed = [Math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
Write-Host ""
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkCyan
Write-Host "  VISION is ready  |  Startup: ${elapsed}s  |  $UI_URL" -ForegroundColor Cyan
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkCyan
Write-Host ""

# Try to open in existing Edge/Chrome first (won't open a new browser if already on the page)
$browsers = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
)
$launched = $false
foreach ($browser in $browsers) {
    if (Test-Path $browser) {
        Start-Process $browser -ArgumentList "--app=$UI_URL --window-size=1400,900"
        ok "Opened in: $(Split-Path $browser -Leaf)"
        $launched = $true
        break
    }
}
if (-not $launched) {
    Start-Process $UI_URL
    ok "Opened in default browser"
}

Write-Host ""
Write-Host "  Logs: $LOG_FILE" -ForegroundColor DarkGray
Write-Host "  Press Ctrl+C to exit this window (server keeps running)" -ForegroundColor DarkGray
Write-Host ""

# Keep window open briefly so user can read startup report
Start-Sleep -Seconds 4
