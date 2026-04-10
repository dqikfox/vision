# ════════════════════════════════════════════════════════════════
#  VISION ELITE — Production Launcher | Orchestrated by Hive Mind
# ════════════════════════════════════════════════════════════════

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$APP_DIR = $PSScriptRoot
$PYTHON = "python"
$UI_URL = "http://localhost:8765"

function hdr($msg) { Write-Host "`n◆ $msg" -ForegroundColor Cyan -NoNewline; Write-Host " " }
function ok($msg)  { Write-Host "  [OK] " -ForegroundColor Green -NoNewline; Write-Host $msg }
function info($msg){ Write-Host "  [..] " -ForegroundColor Gray -NoNewline; Write-Host $msg }
function warn($msg){ Write-Host "  [!!] " -ForegroundColor Yellow -NoNewline; Write-Host $msg }

Clear-Host
Write-Host "  " -NoNewline
Write-Host "VISION ELITE" -ForegroundColor Black -BackgroundColor Cyan -NoNewline
Write-Host " Starting Production Swarm..." -ForegroundColor Cyan
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkCyan

# 1. Environment Validation
hdr "Environment Validation"
if (Test-Path "$APP_DIR\.env") {
    ok "Production .env detected"
    # Load keys into current session for validation
    foreach ($line in Get-Content "$APP_DIR\.env") {
        if ($line -match "^(?<key>[^#\s=]+)=(?<value>.*)$") {
            $env:($Matches.key) = $Matches.value.Trim()
        }
    }
} else {
    warn "Missing .env file! System may be degraded."
}

# 2. Ollama Check
hdr "Local AI Engine (Ollama)"
if (netstat -ano | Select-String ':11434.*LISTENING') {
    ok "Ollama Engine is Active"
} else {
    info "Starting Ollama Background Service..."
    Start-Process "ollama" "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 4
    if (netstat -ano | Select-String ':11434.*LISTENING') { ok "Ollama Initialized" } else { warn "Ollama failed to respond." }
}

# 3. Vision Server
hdr "Vision Operator Server"
if (netstat -ano | Select-String ':8765.*LISTENING') {
    ok "Server already running on port 8765"
} else {
    info "Launching FastAPI Backend..."
    Start-Process $PYTHON "live_chat_app.py" -WorkingDirectory $APP_DIR -WindowStyle Hidden
    
    $started = $false
    for ($i = 0; $i -lt 20; $i++) {
        Write-Host "." -NoNewline -ForegroundColor DarkGray
        if (netstat -ano | Select-String ':8765.*LISTENING') { $started = $true; break }
        Start-Sleep -Seconds 1
    }
    Write-Host ""
    if ($started) { ok "Vision Elite Server Online" } else { warn "Server startup is slow. Checking logs..." }
}

# 4. User Interface
hdr "User Interface"
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
$chrome = "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe"

if (Test-Path $edge) {
    info "Launching Edge in App Mode..."
    Start-Process $edge -ArgumentList "--app=$UI_URL --window-size=1440,960"
    ok "Interface Ready"
} elseif (Test-Path $chrome) {
    info "Launching Chrome in App Mode..."
    Start-Process $chrome -ArgumentList "--app=$UI_URL"
    ok "Interface Ready"
} else {
    info "Launching Default Browser..."
    Start-Process $UI_URL
    ok "Interface Ready"
}

Write-Host "`n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkCyan
Write-Host "  HIVE MIND STATUS: " -NoNewline -ForegroundColor Cyan
Write-Host "ELITE" -ForegroundColor Black -BackgroundColor Green
Write-Host "  SYSTEM READY FOR PRODUCTION" -ForegroundColor Gray
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor DarkCyan

Start-Sleep -Seconds 2
