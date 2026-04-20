#!/usr/bin/env pwsh
# VISION Master Launcher - unified desktop orchestrator
#
# This launcher is the top-level desktop entrypoint. It delegates the core
# service boot to launch_vision.ps1, then performs additional runtime checks and
# opens the monitoring surfaces so the operator and command center come up as a
# single stack.

param(
    [switch]$Reload,
    [switch]$Debug,
    [switch]$SkipBrowser,
    [switch]$SkipOpenClaw
)

$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = "SilentlyContinue"

$REPO_DIR = $PSScriptRoot
$VISION_LAUNCHER = Join-Path $REPO_DIR "launch_vision.ps1"
$UI_URL = "http://localhost:8765"
$COMMAND_CENTER_URL = "$UI_URL/command-center"
$HEALTH_URL = "$UI_URL/api/health"
$DOCTOR_URL = "$UI_URL/api/command-center/doctor"
$MODELS_URL = "$UI_URL/api/models"
$RAG_DATA_ROOT = "G:\rag-v1\data"
$HF_BUCKET_ID = "havikz/bucket"

function ok($msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function err($msg) { Write-Host "  [ERR] $msg" -ForegroundColor Red }
function hdr($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function dot($msg) { Write-Host "  [..] $msg" -ForegroundColor DarkGray }

function Wait-ForHttp([string]$Url, [int]$TimeoutSeconds) {
    for ($i = 0; $i -lt $TimeoutSeconds; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -TimeoutSec 3 -UseBasicParsing
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
                return $true
            }
        } catch {
        }
        Start-Sleep -Seconds 1
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

function Open-Ui([string]$Url) {
    $browsers = @(
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
    )
    foreach ($browser in $browsers) {
        if (Test-Path $browser) {
            Start-Process $browser -ArgumentList "--app=$Url --window-size=1440,960"
            ok "Opened $Url in $(Split-Path $browser -Leaf)"
            return
        }
    }
    Start-Process $Url
    ok "Opened $Url in default browser"
}

Clear-Host
Write-Host ""
Write-Host "  VISION MASTER LAUNCHER" -ForegroundColor Cyan
Write-Host ""
Write-Host "  MASTER LAUNCHER - unified startup, health, and monitoring" -ForegroundColor DarkGray
Write-Host "  ---------------------------------------------------------" -ForegroundColor DarkGray

$startTime = Get-Date

hdr "STEP 1 - Core Vision Stack"
if (-not (Test-Path $VISION_LAUNCHER)) {
    err "Missing launcher: $VISION_LAUNCHER"
    exit 1
}

$launchArgs = @("-NoBrowser")
if ($Reload) { $launchArgs += "-Reload" }
if ($Debug) { $launchArgs += "-Debug" }
dot "Delegating core startup to launch_vision.ps1..."
# launch_vision.ps1 is responsible for starting Ollama (when needed), the
# backend server, and the first round of health/doctor checks.
$launchCommand = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $VISION_LAUNCHER
) + $launchArgs
& powershell @launchCommand
$launchExit = $LASTEXITCODE
if ($launchExit -ne 0) {
    err "launch_vision.ps1 failed with exit code $launchExit"
    exit $launchExit
}
ok "Core Vision launcher completed"

hdr "STEP 2 - Real-Time Service Checks"
# These checks act as the live success indicators for the master launcher after
# the core stack has started.
if (Wait-ForHttp -Url $HEALTH_URL -TimeoutSeconds 20) {
    ok "Health endpoint responding"
    try {
        $health = Invoke-RestMethod -Uri $HEALTH_URL -TimeoutSec 6
        foreach ($name in @("ollama", "browser", "ocr", "gpu", "elevenlabs")) {
            $value = $health.$name
            if ($value -eq $true -or $value -eq "true") {
                ok "$name online"
            } elseif ($value -eq $false -or $value -eq "false") {
                warn "$name offline"
            } else {
                dot "$name => $value"
            }
        }
    } catch {
        warn "Could not parse health payload"
    }
} else {
    err "Health endpoint did not come online in time"
    exit 1
}

if (Wait-ForHttp -Url $DOCTOR_URL -TimeoutSeconds 10) {
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
        warn "Doctor endpoint reachable but payload could not be parsed"
    }
} else {
    warn "Doctor endpoint not yet reachable"
}

if (Wait-ForHttp -Url $MODELS_URL -TimeoutSeconds 10) {
    try {
        $models = Invoke-RestMethod -Uri $MODELS_URL -TimeoutSec 8
        ok "Models endpoint responding"
        ok "Active model: $($models.current_provider)/$($models.current_model)"
    } catch {
        warn "Models endpoint reachable but payload could not be parsed"
    }
} else {
    warn "Models endpoint not yet reachable"
}

hdr "STEP 3 - Supporting Context Surfaces"
# These are not blocking runtime dependencies, but they are important operator
# context surfaces that should be visible during startup.
if (Test-Path $RAG_DATA_ROOT) {
    ok "Local RAG data root present: $RAG_DATA_ROOT"
} else {
    warn "Local RAG data root missing: $RAG_DATA_ROOT"
}
ok "Hugging Face bucket configured for use: $HF_BUCKET_ID"

if (-not $SkipOpenClaw) {
    if (Get-Command openclaw -ErrorAction SilentlyContinue) {
        try {
            $gatewayStatus = & openclaw gateway status 2>&1
            if ($LASTEXITCODE -eq 0) {
                ok "OpenClaw gateway status succeeded"
                $gatewayStatus | ForEach-Object { dot $_ }
            } else {
                warn "OpenClaw gateway status returned a non-zero exit code"
            }
        } catch {
            warn "Could not query OpenClaw gateway status"
        }
    } else {
        warn "OpenClaw CLI not found on PATH"
    }
}

hdr "STEP 4 - Monitoring UIs"
if (-not $SkipBrowser) {
    Open-Ui -Url $UI_URL
    Open-Ui -Url $COMMAND_CENTER_URL
} else {
    dot "Browser launch skipped by -SkipBrowser"
}

$elapsed = [Math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
$lanUrls = Get-LanBaseUrls -Port 8765
$tailscaleUrls = Get-TailscaleBaseUrls -Port 8765
Write-Host ""
Write-Host "  =======================================================" -ForegroundColor DarkCyan
Write-Host "  MASTER STACK READY  |  Startup: ${elapsed}s" -ForegroundColor Cyan
Write-Host "  UI:      $UI_URL" -ForegroundColor DarkGray
Write-Host "  Control: $COMMAND_CENTER_URL" -ForegroundColor DarkGray
if ($lanUrls.Count -gt 0) {
    foreach ($baseUrl in $lanUrls) {
        Write-Host "  LAN UI:  $baseUrl" -ForegroundColor DarkGray
        Write-Host "  LAN Ctl: $baseUrl/command-center" -ForegroundColor DarkGray
    }
}
if ($tailscaleUrls.Count -gt 0) {
    foreach ($baseUrl in $tailscaleUrls) {
        Write-Host "  Tail UI: $baseUrl" -ForegroundColor DarkGray
        Write-Host "  Tail Ctl:$baseUrl/command-center" -ForegroundColor DarkGray
    }
}
Write-Host "  RAG:     $RAG_DATA_ROOT" -ForegroundColor DarkGray
Write-Host "  Bucket:  $HF_BUCKET_ID" -ForegroundColor DarkGray
Write-Host "  =======================================================" -ForegroundColor DarkCyan
Write-Host ""
