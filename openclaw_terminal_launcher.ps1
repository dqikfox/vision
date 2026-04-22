#!/usr/bin/env pwsh
# OpenClaw Terminal Launcher for native Windows.
# Starts/validates Ollama, repairs known OpenClaw config issues, starts the
# gateway, and opens the terminal UI with clear status indicators.

param(
    [string]$ModelId = "kimi-k2.5:cloud",
    [switch]$ValidateOnly,
    [switch]$NoTui,
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepoDir = $PSScriptRoot
$PowerShellExe = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source
$OllamaExe = (Get-Command ollama -ErrorAction SilentlyContinue).Source
$OpenClawExe = (Get-Command openclaw -ErrorAction SilentlyContinue).Source
$UserHome = [Environment]::GetFolderPath("UserProfile")
$OpenClawHome = Join-Path $UserHome ".openclaw"
$OpenClawConfigPath = Join-Path $OpenClawHome "openclaw.json"
$OllamaBaseUrl = "http://127.0.0.1:11434"
$OllamaHost = "0.0.0.0:11434"   # bind all interfaces so Tailscale clients can reach Ollama
$GatewayPort = 18789
$GatewayWsUrl = "ws://100.83.120.56:$GatewayPort"

# Ensure OPENCLAW_ALLOW_INSECURE_PRIVATE_WS is set for tailnet-bound gateway (ws:// over Tailscale VPN).
# Set in both current session and user persistent env so the service/task inherits it on reboot.
$env:OPENCLAW_ALLOW_INSECURE_PRIVATE_WS = "1"
if ([Environment]::GetEnvironmentVariable("OPENCLAW_ALLOW_INSECURE_PRIVATE_WS", "User") -ne "1") {
    [Environment]::SetEnvironmentVariable("OPENCLAW_ALLOW_INSECURE_PRIVATE_WS", "1", "User")
}

# If OLLAMA_MODELS points to an unavailable drive (e.g. external SSD), create a subst so
# Ollama can start. Ollama reads OLLAMA_MODELS from the Windows machine registry directly —
# setting $env:OLLAMA_MODELS has no effect — so subst is the reliable workaround.
$sysMods = [Environment]::GetEnvironmentVariable("OLLAMA_MODELS", "Machine")
if ($sysMods) {
    $modsQualifier = Split-Path $sysMods -Qualifier   # e.g. "F:"
    if ($modsQualifier -and -not (Test-Path $modsQualifier)) {
        $substTarget = Join-Path $UserHome ".ollama"
        Write-Host "  [WARN] OLLAMA_MODELS drive $modsQualifier unavailable. Creating subst $modsQualifier -> $substTarget" -ForegroundColor Yellow
        & subst $modsQualifier $substTarget 2>$null | Out-Null
        if (Test-Path $modsQualifier) {
            Write-Host "  [OK]   subst $modsQualifier created for this session" -ForegroundColor DarkGray
        } else {
            Write-Host "  [ERR]  subst $modsQualifier failed — Ollama may not start" -ForegroundColor Red
        }
    }
}

function ok($msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function err($msg) { Write-Host "  [ERR] $msg" -ForegroundColor Red }
function hdr($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function dot($msg) { Write-Host "  [..] $msg" -ForegroundColor DarkGray }

function Test-ListeningPort([int]$Port) {
    return [bool](netstat -ano | Select-String -Pattern ":$Port\b.*LISTENING")
}

function Wait-ForPort([int]$Port, [int]$TimeoutSeconds) {
    for ($i = 0; $i -lt $TimeoutSeconds; $i++) {
        if (Test-ListeningPort -Port $Port) {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Wait-ForHttp([string]$Url, [int]$TimeoutSeconds) {
    for ($i = 0; $i -lt $TimeoutSeconds; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 3 -UseBasicParsing
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Ensure-Property([object]$Object, [string]$Name, [object]$DefaultValue) {
    if ($null -eq $Object.PSObject.Properties[$Name]) {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $DefaultValue
        return $true
    }
    if ($null -eq $Object.$Name) {
        $Object.$Name = $DefaultValue
        return $true
    }
    return $false
}

function Start-ManagedConsole(
    [string]$Title,
    [string]$CommandText,
    [ValidateSet("Normal", "Minimized")]
    [string]$WindowStyle = "Normal"
) {
    $safeTitle = $Title.Replace("'", "''")
    $commandBlock = "& { `$Host.UI.RawUI.WindowTitle = '$safeTitle'; Set-Location '$RepoDir'; $CommandText }"
    Start-Process -FilePath $PowerShellExe `
        -WorkingDirectory $RepoDir `
        -WindowStyle $WindowStyle `
        -ArgumentList @(
            "-NoExit",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command", $commandBlock
        ) | Out-Null
}

function Invoke-OpenClawDoctorFix([string]$CliPath, [int]$TimeoutSeconds = 20) {
    $stdoutPath = Join-Path $env:TEMP "openclaw-doctor-stdout.txt"
    $stderrPath = Join-Path $env:TEMP "openclaw-doctor-stderr.txt"
    Remove-Item $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue

    # If the CLI resolved to a .ps1 script (npm-installed shim on Windows),
    # we must host it via powershell.exe rather than Start-Process -FilePath directly.
    $isPsScript = $CliPath -match '\.ps1$'
    if ($isPsScript) {
        $startArgs = @{
            FilePath               = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source ?? "powershell.exe"
            ArgumentList           = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $CliPath, "doctor", "--fix")
            RedirectStandardOutput = $stdoutPath
            RedirectStandardError  = $stderrPath
            WindowStyle            = "Hidden"
            PassThru               = $true
        }
    } else {
        $startArgs = @{
            FilePath               = $CliPath
            ArgumentList           = @("doctor", "--fix")
            RedirectStandardOutput = $stdoutPath
            RedirectStandardError  = $stderrPath
            WindowStyle            = "Hidden"
            PassThru               = $true
        }
    }
    $process = Start-Process @startArgs

    $completed = $true
    try {
        Wait-Process -Id $process.Id -Timeout $TimeoutSeconds -ErrorAction Stop
    } catch {
        $completed = $false
    }

    if (-not $completed) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        warn "OpenClaw doctor --fix timed out after ${TimeoutSeconds}s; continuing with launcher-safe defaults"
        return
    }

    $doctorOutput = @()
    if (Test-Path $stdoutPath) {
        $doctorOutput += Get-Content $stdoutPath
    }
    if (Test-Path $stderrPath) {
        $doctorOutput += Get-Content $stderrPath
    }

    if ($process.ExitCode -eq 0) {
        ok "OpenClaw doctor --fix completed"
    } else {
        warn "OpenClaw doctor --fix reported issues"
    }
    foreach ($line in $doctorOutput) {
        if ("$line".Trim()) {
            dot "$line"
        }
    }

    Remove-Item $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
}

function Ensure-OpenClawConfig([string]$ConfigPath, [string]$PrimaryModel) {
    if (-not (Test-Path $ConfigPath)) {
        warn "OpenClaw config not found yet: $ConfigPath"
        warn "The launcher will rely on onboard to create it when needed."
        return $false
    }

    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    $changed = $false

    if (Ensure-Property -Object $config -Name "agents" -DefaultValue ([pscustomobject]@{})) { $changed = $true }
    if (Ensure-Property -Object $config.agents -Name "defaults" -DefaultValue ([pscustomobject]@{})) { $changed = $true }
    if (Ensure-Property -Object $config.agents.defaults -Name "model" -DefaultValue ([pscustomobject]@{})) { $changed = $true }
    if ([string]::IsNullOrWhiteSpace("$($config.agents.defaults.model.primary)")) {
        $config.agents.defaults.model.primary = $PrimaryModel
        $changed = $true
    }

    if (Ensure-Property -Object $config -Name "gateway" -DefaultValue ([pscustomobject]@{})) { $changed = $true }
    if ([string]::IsNullOrWhiteSpace("$($config.gateway.mode)")) {
        $config.gateway.mode = "local"
        $changed = $true
    }
    if ("$($config.gateway.bind)" -notin @("loopback", "custom", "tailnet", "lan", "auto")) {
        $config.gateway.bind = "loopback"
        $changed = $true
    }
    if (Ensure-Property -Object $config.gateway -Name "port" -DefaultValue $GatewayPort) { $changed = $true }

    if (Ensure-Property -Object $config -Name "models" -DefaultValue ([pscustomobject]@{})) { $changed = $true }
    if (Ensure-Property -Object $config.models -Name "providers" -DefaultValue ([pscustomobject]@{})) { $changed = $true }
    if ($null -ne $config.models.providers.ollama) {
        if ([string]::IsNullOrWhiteSpace("$($config.models.providers.ollama.baseUrl)")) {
            $config.models.providers.ollama.baseUrl = $OllamaBaseUrl
            $changed = $true
        }
    }

    if (-not $changed) {
        return $false
    }

    $backupPath = "$ConfigPath.launcher.bak"
    Copy-Item -Path $ConfigPath -Destination $backupPath -Force
    $config | ConvertTo-Json -Depth 100 | Set-Content -Path $ConfigPath -Encoding UTF8
    ok "Normalized OpenClaw config for local Windows launcher"
    dot "Backup written to $backupPath"
    return $true
}

function Show-FinalStatus([bool]$OllamaReady, [bool]$GatewayReady, [bool]$TuiStarted, [string]$Model) {
    Write-Host ""
    Write-Host "  =======================================================" -ForegroundColor DarkCyan
    if ($OllamaReady -and $GatewayReady) {
        Write-Host "  OPENCLAW TERMINAL STACK READY" -ForegroundColor Cyan
    } else {
        Write-Host "  OPENCLAW TERMINAL STACK PARTIAL" -ForegroundColor Yellow
    }
    Write-Host "  Ollama : $(if ($OllamaReady) { 'READY' } else { 'NOT READY' })" -ForegroundColor DarkGray
    Write-Host "  Gateway: $(if ($GatewayReady) { 'READY' } else { 'NOT READY' })" -ForegroundColor DarkGray
    Write-Host "  TUI    : $(if ($TuiStarted) { 'OPENED' } else { 'NOT OPENED' })" -ForegroundColor DarkGray
    Write-Host "  Model  : $Model" -ForegroundColor DarkGray
    Write-Host "  Config : $OpenClawConfigPath" -ForegroundColor DarkGray
    Write-Host "  Gateway: $GatewayWsUrl" -ForegroundColor DarkGray
    Write-Host "  =======================================================" -ForegroundColor DarkCyan
    Write-Host ""
}

Clear-Host
Write-Host ""
Write-Host "  OPENCLAW TERMINAL LAUNCHER" -ForegroundColor Cyan
Write-Host "  Native Windows startup for Ollama + Gateway + TUI" -ForegroundColor DarkGray
Write-Host ""

$ollamaReady = $false
$gatewayReady = $false
$tuiStarted = $false
$primaryModel = "ollama/$ModelId"

hdr "STEP 1 - Prerequisites"
if (-not $PowerShellExe) {
    err "powershell.exe is not available"
    exit 1
}
if (-not $OllamaExe) {
    err "Ollama is not available on PATH"
    exit 1
}
if (-not $OpenClawExe) {
    err "OpenClaw is not available on PATH"
    exit 1
}
ok "Ollama CLI found"
ok "OpenClaw CLI found"

hdr "STEP 2 - OpenClaw Config"
$null = Ensure-OpenClawConfig -ConfigPath $OpenClawConfigPath -PrimaryModel $primaryModel
Invoke-OpenClawDoctorFix -CliPath $OpenClawExe

hdr "STEP 3 - Ollama"
# Detect if Ollama is running but bound to loopback only (prevents Tailscale access)
$ollamaLoopbackOnly = $false
if (Wait-ForHttp -Url "$OllamaBaseUrl/api/tags" -TimeoutSeconds 2) {
    $ollamaBinds = netstat -ano | Select-String ":11434.*LISTEN"
    $isAllInterfaces = $ollamaBinds | Select-String "0\.0\.0\.0:11434"
    if ($isAllInterfaces) {
        ok "Ollama is already responding and bound to all interfaces"
        $ollamaReady = $true
    } else {
        warn "Ollama is responding but bound to loopback only — restarting with $OllamaHost"
        $ollamaLoopbackOnly = $true
        # Kill existing loopback-bound Ollama
        $ollamaPid = ($ollamaBinds | Select-Object -First 1) -replace '.*LISTENING\s+(\d+).*', '$1'
        if ($ollamaPid -match '^\d+$') {
            Stop-Process -Id ([int]$ollamaPid) -Force -ErrorAction SilentlyContinue
            Start-Sleep 2
        }
    }
}

if (-not $ollamaReady -and -not $ValidateOnly) {
    dot "Starting Ollama in its own PowerShell window..."
    # Repeat the subst in the spawned window so Ollama can access its model path
    $substLine = if ($sysMods -and (Split-Path $sysMods -Qualifier)) {
        $q = Split-Path $sysMods -Qualifier
        "subst $q `"$UserHome\.ollama`" 2>`$null | Out-Null; Start-Sleep 1"
    } else { "" }
    Start-ManagedConsole -Title "OpenClaw Launcher - Ollama" -WindowStyle "Minimized" -CommandText @"
`$env:OLLAMA_HOST = '$OllamaHost'
$substLine
ollama serve
"@
    if (Wait-ForHttp -Url "$OllamaBaseUrl/api/tags" -TimeoutSeconds 25) {
        ok "Ollama started successfully"
        $ollamaReady = $true
    } else {
        err "Ollama did not come online at $OllamaBaseUrl"
    }
} elseif ($ValidateOnly -and -not $ollamaReady) {
    warn "ValidateOnly: Ollama is not running"
}

try {
    $ollamaModels = & $OllamaExe list 2>&1
    if ($LASTEXITCODE -eq 0) {
        if ($ollamaModels | Select-String -SimpleMatch $ModelId) {
            ok "Model reference detected: $ModelId"
        } else {
            warn "Model '$ModelId' was not listed by Ollama; on-demand/cloud resolution may still work"
        }
    }
} catch {
    warn "Could not query Ollama model list"
}

hdr "STEP 4 - OpenClaw Gateway"
# Always kill any existing gateway so the fresh config (e.g. updated Ollama baseUrl, bind mode)
# is loaded. The gateway does NOT hot-reload config changes — stale processes use old settings.
$gwNetstatLine = (netstat -ano | Select-String ":$GatewayPort.*LISTEN" | Select-Object -First 1).Line
$gwPid = $null
if ($gwNetstatLine -and $gwNetstatLine -match '\s(\d+)\s*$') {
    $gwPid = [int]$Matches[1]
}
if ($gwPid) {
    dot "Stopping existing gateway (PID $gwPid) to apply latest config..."
    taskkill /PID $gwPid /F 2>$null | Out-Null
    schtasks /End /TN "OpenClaw Gateway" 2>$null | Out-Null
    Start-Sleep -Seconds 2
}
# Clear stale lock files so openclaw gateway run doesn't refuse to start
Get-ChildItem "$env:TEMP\openclaw" -Filter "gateway*.lock" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

if ($ValidateOnly) {
    warn "ValidateOnly: gateway not started"
} else {
    dot "Starting OpenClaw gateway (node.exe direct — bypasses lock conflicts)..."
    $nodeExePath = (Get-Command node.exe -ErrorAction SilentlyContinue).Source ?? "node.exe"
    $ocModulePath = "$env:APPDATA\npm\node_modules\openclaw\dist\index.js"
    # OPENCLAW_ALLOW_INSECURE_PRIVATE_WS is already set in $env: above; child processes inherit it.
    Start-Process -FilePath $nodeExePath `
        -ArgumentList "`"$ocModulePath`"", "gateway", "run" `
        -WindowStyle Hidden | Out-Null
    if (Wait-ForPort -Port $GatewayPort -TimeoutSeconds 60) {
        ok "OpenClaw gateway started successfully"
        $gatewayReady = $true
    } else {
        err "OpenClaw gateway did not start on port $GatewayPort"
    }
}

hdr "STEP 5 - Terminal Chat UI"
if ($NoTui) {
    warn "TUI launch skipped by -NoTui"
} elseif ($ValidateOnly) {
    warn "ValidateOnly: TUI launch skipped"
} elseif ($gatewayReady) {
    Start-ManagedConsole -Title "OpenClaw TUI" -WindowStyle "Normal" -CommandText @"
openclaw tui
"@
    ok "OpenClaw TUI launched"
    $tuiStarted = $true
} else {
    warn "TUI not launched because the gateway is not ready"
}

Show-FinalStatus -OllamaReady $ollamaReady -GatewayReady $gatewayReady -TuiStarted $tuiStarted -Model $primaryModel

if (-not $NoPause) {
    Read-Host "Press Enter to close the launcher window"
}
