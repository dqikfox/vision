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
$OllamaHost = "127.0.0.1:11434"
$GatewayPort = 18789
$GatewayWsUrl = "ws://127.0.0.1:$GatewayPort"

function ok($msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function err($msg) { Write-Host "  [ERR] $msg" -ForegroundColor Red }
function hdr($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function dot($msg) { Write-Host "  [..] $msg" -ForegroundColor DarkGray }

function Test-ListeningPort([int]$Port) {
    return [bool](netstat -ano | Select-String -Pattern "LISTENING\s*$" | Select-String -Pattern ":$Port\b")
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

    $process = Start-Process -FilePath $CliPath `
        -ArgumentList @("doctor", "--fix") `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -WindowStyle Hidden `
        -PassThru

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
    if ("$($config.gateway.bind)" -notin @("loopback", "custom")) {
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
if (Wait-ForHttp -Url "$OllamaBaseUrl/api/tags" -TimeoutSeconds 2) {
    ok "Ollama is already responding at $OllamaBaseUrl"
    $ollamaReady = $true
} elseif ($ValidateOnly) {
    warn "ValidateOnly: Ollama is not running"
} else {
    dot "Starting Ollama in its own PowerShell window..."
    Start-ManagedConsole -Title "OpenClaw Launcher - Ollama" -WindowStyle "Minimized" -CommandText @"
`$env:OLLAMA_HOST = '$OllamaHost'
ollama serve
"@
    if (Wait-ForHttp -Url "$OllamaBaseUrl/api/tags" -TimeoutSeconds 25) {
        ok "Ollama started successfully"
        $ollamaReady = $true
    } else {
        err "Ollama did not come online at $OllamaBaseUrl"
    }
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
if (Wait-ForPort -Port $GatewayPort -TimeoutSeconds 2) {
    ok "OpenClaw gateway is already listening on port $GatewayPort"
    $gatewayReady = $true
} elseif ($ValidateOnly) {
    warn "ValidateOnly: gateway is not running"
} else {
    dot "Starting OpenClaw gateway in its own PowerShell window..."
    Start-ManagedConsole -Title "OpenClaw Launcher - Gateway" -WindowStyle "Minimized" -CommandText @"
openclaw gateway run
"@
    if (Wait-ForPort -Port $GatewayPort -TimeoutSeconds 25) {
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
