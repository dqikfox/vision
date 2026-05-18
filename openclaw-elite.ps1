# OpenClaw Elite Dev Launcher
# Usage:
#   .\openclaw-elite.ps1                    # Launch Copilot CLI with OpenClaw
#   .\openclaw-elite.ps1 -Verify            # Verify OpenClaw API health
#   .\openclaw-elite.ps1 -Diagnostics       # Full diagnostic report
#   .\openclaw-elite.ps1 -Model fast        # Use fast model (gpt-4o-mini)
#   .\openclaw-elite.ps1 -Model power       # Use power model (claude-sonnet-4)
#   .\openclaw-elite.ps1 -VisionCheck       # Check Vision backend health
#   .\openclaw-elite.ps1 -Quick             # Skip all checks, fast launch

param(
    [switch]$Verify,
    [switch]$Diagnostics,
    [switch]$VisionCheck,
    [switch]$Quick,
    [string]$Model = "default",
    [switch]$Help,
    [switch]$Status,
    [switch]$Fix,
    [switch]$Config,
    [switch]$Interactive,
    [string]$SessionName = "",
    [switch]$Memory,
    [switch]$SelfAwareness
)

# ── Configuration ─────────────────────────────────────────────────────────────
$script:Version = "1.1.0"
$script:ConfigPath = Join-Path $env:USERPROFILE '.openclaw\openclaw.json'
$script:EliteConfigPath = Join-Path $PSScriptRoot 'openclaw-elite-config.json'
$script:VisionUrl = "http://localhost:8765"
$script:SessionLogPath = Join-Path $env:USERPROFILE '.openclaw\elite-sessions.log'

# Color scheme
$Colors = @{
    Success = 'Green'
    Info = 'Cyan'
    Warning = 'Yellow'
    Error = 'Red'
    Accent = 'Magenta'
    Dim = 'DarkGray'
    Elite = 'DarkCyan'
    Phone = 'DarkYellow'
    Memory = 'DarkCyan'
}

# ── Helper Functions ─────────────────────────────────────────────────────────
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

function Write-Section($Title) {
    Write-Host ""
    Write-Host "── $Title ──" -ForegroundColor $Colors.Accent
}

function Test-Command($Command) {
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-OpenClawConfig {
    if (-not (Test-Path $script:ConfigPath)) {
        return $null
    }
    try {
        return Get-Content -Raw $script:ConfigPath | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Get-EliteConfig {
    if (-not (Test-Path $script:EliteConfigPath)) {
        return $null
    }
    try {
        $config = Get-Content -Raw $script:EliteConfigPath | ConvertFrom-Json
        $backendUrl = $config.elite.vision.backend_url
        if ($backendUrl -eq 'USE_ENV_BACKEND_URL') {
            $backendUrl = $env:BACKEND_URL
            if ([string]::IsNullOrWhiteSpace($backendUrl)) {
                throw 'BACKEND_URL must be set when elite.vision.backend_url uses USE_ENV_BACKEND_URL.'
            }
            $config.elite.vision.backend_url = $backendUrl
        }
        if (-not [string]::IsNullOrWhiteSpace($config.elite.vision.backend_url)) {
            $script:VisionUrl = $config.elite.vision.backend_url
        }
        return $config
    } catch {
        Write-Status "Failed to load elite config: $_" 'Warning'
        return $null
    }
}

# ── Diagnostic Functions ─────────────────────────────────────────────────────
function Test-OpenClawGateway {
    param([hashtable]$Config)

    $bind = if ($Config.gateway.bind) { $Config.gateway.bind } else { "loopback" }
    $port = if ($Config.gateway.port) { $Config.gateway.port } else { 18789 }

    # Handle bind modes
    $baseUrl = switch ($bind) {
        'lan' { "http://127.0.0.1:$port" }
        'loopback' { "http://127.0.0.1:$port" }
        '0.0.0.0' { "http://127.0.0.1:$port" }
        default { "http://$bind`:$port" }
    }

    $headers = @{ Authorization = "Bearer $($Config.gateway.auth.token)" }

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Headers $headers -Uri "$baseUrl/v1/models" -TimeoutSec 5
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            BaseUrl = $baseUrl
            Response = $response.Content | ConvertFrom-Json
        }
    } catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
            BaseUrl = $baseUrl
        }
    }
}

function Test-VisionBackend {
    try {
        $response = Invoke-WebRequest -Uri "$script:VisionUrl/api/health" -TimeoutSec 5
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Response = $response.Content | ConvertFrom-Json
        }
    } catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

function Get-GatewayStatus {
    try {
        $output = & openclaw gateway status --json 2>$null | ConvertFrom-Json
        return $output
    } catch {
        return $null
    }
}

# ── Main Functions ───────────────────────────────────────────────────────────
function Show-Help {
    @"
🦞 OpenClaw Elite Dev Launcher v$script:Version

USAGE:
    .\openclaw-elite.ps1 [OPTIONS]

OPTIONS:
    -Verify          Verify OpenClaw API health and exit
    -Diagnostics     Run full diagnostic report
    -VisionCheck     Check Vision backend health
    -Status          Show quick status overview
    -Fix             Run openclaw doctor --fix
    -Config          Show current configuration
    -Interactive     Interactive mode with menu
    -Model <name>    Select model (default, fast, power, local)
    -SessionName <n> Name for this session (logged to elite-sessions.log)
    -Quick           Skip all checks, fast launch
    -Help            Show this help message

MODELS:
    default          OpenClaw default model
    fast             GPT-4o-mini for quick tasks
    power            Claude Sonnet 4 for complex work
    local            Local Ollama model

EXAMPLES:
    .\openclaw-elite.ps1 -Diagnostics
    .\openclaw-elite.ps1 -Model power -SessionName "CodeReview"
    .\openclaw-elite.ps1 -Interactive
    .\openclaw-elite.ps1 -Status
    .\openclaw-elite.ps1 -Fix
"@ | Write-Host
}

function Show-Banner {
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║     🦞 OpenClaw Elite Dev Environment v$script:Version              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $Colors.Accent
}

function Show-Diagnostics {
    Write-Section "System Diagnostics"

    # Check Node.js
    if (Test-Command 'node') {
        $nodeVersion = & node --version
        Write-Status "Node.js $nodeVersion" 'Success'
    } else {
        Write-Status "Node.js not found" 'Error'
    }

    # Check OpenClaw CLI
    if (Test-Command 'openclaw') {
        $ocVersion = & openclaw --version
        Write-Status "OpenClaw $ocVersion" 'Success'
    } else {
        Write-Status "OpenClaw CLI not found" 'Error'
    }

    # Check Copilot CLI
    if (Test-Command 'copilot') {
        Write-Status "GitHub Copilot CLI available" 'Success'
    } else {
        Write-Status "GitHub Copilot CLI not found (run: gh copilot install)" 'Warning'
    }

    Write-Section "OpenClaw Configuration"

    $config = Get-OpenClawConfig
    if ($config) {
        Write-Status "Config found at $script:ConfigPath" 'Success'

        $bind = if ($config.gateway.bind) { $config.gateway.bind } else { "loopback" }
        $port = if ($config.gateway.port) { $config.gateway.port } else { 18789 }
        Write-Status "Gateway bind: $bind, port: $port" 'Info'

        if ($config.gateway.auth.token) {
            $tokenPreview = $config.gateway.auth.token.Substring(0, [Math]::Min(8, $config.gateway.auth.token.Length)) + "..."
            Write-Status "Auth token: $tokenPreview" 'Success'
        } else {
            Write-Status "Auth token missing" 'Error'
        }
    } else {
        Write-Status "OpenClaw config not found" 'Error'
        return
    }

    Write-Section "Gateway Health"

    $status = Get-GatewayStatus
    if ($status) {
        if ($status.health.healthy) {
            Write-Status "Gateway is healthy" 'Success'
        } else {
            Write-Status "Gateway has health issues" 'Warning'
        }

        if ($status.service.runtime.status -eq 'running') {
            Write-Status "Service running (PID: $($status.service.runtime.pid))" 'Success'
        } else {
            Write-Status "Service not running" 'Error'
        }

        Write-Status "Port $($status.port.port): $($status.port.status)" $(if ($status.port.status -eq 'busy') { 'Success' } else { 'Warning' })
    } else {
        Write-Status "Could not retrieve gateway status" 'Error'
    }

    Write-Section "API Verification"

    $apiTest = Test-OpenClawGateway -Config $config
    if ($apiTest.Success) {
        Write-Status "API responding ($($apiTest.StatusCode))" 'Success'
        Write-Status "Available models: $($apiTest.Response.data.Count)" 'Info'
        foreach ($m in $apiTest.Response.data | Select-Object -First 3) {
            Write-Host "    • $($m.id)" -ForegroundColor $Colors.Dim
        }
    } else {
        Write-Status "API check failed: $($apiTest.Error)" 'Error'
    }

    Write-Section "Vision Backend"

    $visionTest = Test-VisionBackend
    if ($visionTest.Success) {
        Write-Status "Vision backend healthy" 'Success'
        Write-Status "Status: $($visionTest.Response.status)" 'Info'
    } else {
        Write-Status "Vision backend not responding: $($visionTest.Error)" 'Warning'
    }
}

function Invoke-OpenClawCLI {
    param([string]$SelectedModel = 'default')

    $config = Get-OpenClawConfig
    if (-not $config) {
        throw "OpenClaw config not found at $script:ConfigPath"
    }

    $gatewayToken = $config.gateway.auth.token
    if ([string]::IsNullOrWhiteSpace($gatewayToken)) {
        throw 'OpenClaw gateway token is missing from config'
    }

    # Determine base URL
    $bind = if ($config.gateway.bind) { $config.gateway.bind } else { "loopback" }
    $port = if ($config.gateway.port) { $config.gateway.port } else { 18789 }

    $baseUrl = switch ($bind) {
        'lan' { "http://127.0.0.1:$port/v1" }
        'loopback' { "http://127.0.0.1:$port/v1" }
        '0.0.0.0' { "http://127.0.0.1:$port/v1" }
        default { "http://$bind`:$port/v1" }
    }

    # Get model from elite config if available
    $eliteConfig = Get-EliteConfig
    $model = if ($eliteConfig -and $eliteConfig.elite.models.$SelectedModel) {
        $eliteConfig.elite.models.$SelectedModel
    } else {
        'openclaw/default'
    }

    # Set environment variables
    $env:OPENCLAW_GATEWAY_TOKEN = $gatewayToken
    $env:COPILOT_PROVIDER_TYPE = 'openai'
    $env:COPILOT_PROVIDER_BASE_URL = $baseUrl
    $env:COPILOT_PROVIDER_API_KEY = $gatewayToken
    $env:COPILOT_MODEL = $model

    Write-Section "Launch Configuration"
    Write-Status "Gateway URL: $baseUrl" 'Info'
    Write-Status "Model: $model" 'Info'
    Write-Status "Token: configured" 'Success'

    if (-not (Test-Command 'copilot')) {
        throw 'GitHub Copilot CLI is not installed. Run: gh copilot install'
    }

    Write-Host ""
    Write-Status "Launching GitHub Copilot CLI..." 'Accent'
    Write-Host ""

    & copilot
}

function Show-Status {
    Write-Section "Quick Status"

    # System checks
    $nodeOk = Test-Command 'node'
    $ocOk = Test-Command 'openclaw'
    $copilotOk = Test-Command 'copilot'

    Write-Status "Node.js: $(if ($nodeOk) { '✓' } else { '✗' })" $(if ($nodeOk) { 'Success' } else { 'Error' })
    Write-Status "OpenClaw: $(if ($ocOk) { '✓' } else { '✗' })" $(if ($ocOk) { 'Success' } else { 'Error' })
    Write-Status "Copilot CLI: $(if ($copilotOk) { '✓' } else { '✗' })" $(if ($copilotOk) { 'Success' } else { 'Error' })

    # Gateway status
    $status = Get-GatewayStatus
    if ($status -and $status.health.healthy) {
        Write-Status "Gateway: Running (PID $($status.service.runtime.pid))" 'Success'
        Write-Status "Port $($status.port.port): $($status.port.status)" 'Info'
    } else {
        Write-Status "Gateway: Not running or unhealthy" 'Warning'
    }

    # Vision status
    $vision = Test-VisionBackend
    if ($vision.Success) {
        Write-Status "Vision: $($vision.Response.status)" 'Success'
    } else {
        Write-Status "Vision: Not responding" 'Warning'
    }
}

function Show-Config {
    Write-Section "OpenClaw Configuration"

    $config = Get-OpenClawConfig
    if (-not $config) {
        Write-Status "Config not found at $script:ConfigPath" 'Error'
        return
    }

    Write-Status "Config path: $script:ConfigPath" 'Info'
    Write-Status "Gateway bind: $($config.gateway.bind)" 'Info'
    Write-Status "Gateway port: $($config.gateway.port)" 'Info'
    Write-Status "Auth token: $(if ($config.gateway.auth.token) { 'configured' } else { 'missing!' })" $(if ($config.gateway.auth.token) { 'Success' } else { 'Error' })

    Write-Section "Elite Configuration"
    $elite = Get-EliteConfig
    if ($elite) {
        Write-Status "Elite config found" 'Success'
        Write-Host ""
        Write-Host "Available Models:" -ForegroundColor $Colors.Accent
        $elite.elite.models.PSObject.Properties | ForEach-Object {
            Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor $Colors.Info
        }
    } else {
        Write-Status "Elite config not found (using defaults)" 'Warning'
    }
}

function Invoke-Fix {
    Write-Section "Running OpenClaw Doctor Fix"
    Write-Status "This will migrate legacy config keys..." 'Warning'
    Write-Host ""
    & openclaw doctor --fix
}

function Write-SessionLog($Model, $SessionName) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$timestamp] Session started | Model: $Model | Name: $SessionName"
    Add-Content -Path $script:SessionLogPath -Value $entry -ErrorAction SilentlyContinue
}

function Show-InteractiveMenu {
    while ($true) {
        Clear-Host
        Show-Banner
        Write-Host ""
        Write-Host "  [1] Launch Copilot (Default Model)" -ForegroundColor $Colors.Info
        Write-Host "  [2] Launch Copilot (Fast Model)" -ForegroundColor $Colors.Info
        Write-Host "  [3] Launch Copilot (Power Model)" -ForegroundColor $Colors.Info
        Write-Host "  [4] Elite Tools Menu" -ForegroundColor $Colors.Accent
        Write-Host "  [5] Phone Control 📱" -ForegroundColor $Colors.Phone
        Write-Host "  [6] Memory & Self-Awareness 🧠" -ForegroundColor $Colors.Memory
        Write-Host "  [7] Run Diagnostics" -ForegroundColor $Colors.Info
        Write-Host "  [8] Quick Status Check" -ForegroundColor $Colors.Info
        Write-Host "  [9] Show Configuration" -ForegroundColor $Colors.Info
        Write-Host "  [10] Fix Config Issues" -ForegroundColor $Colors.Warning
        Write-Host "  [11] Verify API" -ForegroundColor $Colors.Info
        Write-Host "  [12] Check Vision Backend" -ForegroundColor $Colors.Info
        Write-Host "  [13] Ultron Azure AI ⚡" -ForegroundColor DarkMagenta
        Write-Host "  [Q] Quit" -ForegroundColor $Colors.Dim
        Write-Host ""

        $choice = Read-Host "Select option"

        switch ($choice) {
            '1' { Invoke-OpenClawCLI -SelectedModel 'default'; return }
            '2' { Invoke-OpenClawCLI -SelectedModel 'fast'; return }
            '3' { Invoke-OpenClawCLI -SelectedModel 'power'; return }
            '4' { Invoke-EliteToolsMenu }
            '5' { Invoke-PhoneControl }
            '6' { Invoke-MemorySystem }
            '7' { Show-Diagnostics; Write-Host ""; Read-Host "Press Enter to continue" }
            '8' { Show-Status; Write-Host ""; Read-Host "Press Enter to continue" }
            '9' { Show-Config; Write-Host ""; Read-Host "Press Enter to continue" }
            '10' { Invoke-Fix; Write-Host ""; Read-Host "Press Enter to continue" }
            '11' {
                $config = Get-OpenClawConfig
                if ($config) {
                    $apiTest = Test-OpenClawGateway -Config $config
                    if ($apiTest.Success) {
                        Write-Status "API OK ($($apiTest.StatusCode))" 'Success'
                    } else {
                        Write-Status "API Failed: $($apiTest.Error)" 'Error'
                    }
                }
                Read-Host "Press Enter to continue"
            }
            '12' {
                $vision = Test-VisionBackend
                if ($vision.Success) {
                    Write-Status "Vision OK: $($vision.Response.status)" 'Success'
                } else {
                    Write-Status "Vision Failed: $($vision.Error)" 'Error'
                }
                Read-Host "Press Enter to continue"
            }
            'q' { return }
            'Q' { return }
        }
    }
}

function Invoke-PhoneControl {
    $scriptPath = Join-Path $PSScriptRoot 'openclaw-elite-phone.ps1'
    if (-not (Test-Path $scriptPath)) {
        Write-Status "Phone control script not found: $scriptPath" 'Error'
        return
    }
    try {
        Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'RemoteSigned', '-File', $scriptPath, '-Interactive') | Out-Null
    } catch {
        Write-Status "Phone control failed: $_" 'Error'
    }
}

function Invoke-MemorySystem {
    $scriptPath = Join-Path $PSScriptRoot 'openclaw-elite-memory.ps1'
    if (-not (Test-Path $scriptPath)) {
        Write-Status "Memory system script not found: $scriptPath" 'Error'
        return
    }
    try {
        Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'RemoteSigned', '-File', $scriptPath) | Out-Null
    } catch {
        Write-Status "Memory system failed: $_" 'Error'
    }
}

function Show-McpStatus {
    Write-Section "MCP Servers Status"

    $mcpServers = @(
        @{ Name = "filesystem"; Required = $true },
        @{ Name = "github"; Required = $true },
        @{ Name = "memory"; Required = $true },
        @{ Name = "sequential-thinking"; Required = $true },
        @{ Name = "brave-search"; Required = $false },
        @{ Name = "fetch"; Required = $true },
        @{ Name = "puppeteer"; Required = $true },
        @{ Name = "pdf"; Required = $true }
    )

    foreach ($server in $mcpServers) {
        $installed = $false
        try {
            npx -y "@modelcontextprotocol/server-$($server.Name)" --version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { $installed = $true }
        } catch {}

        if ($installed) {
            Write-Status "MCP $($server.Name): installed" 'Success'
        } else {
            if ($server.Required) {
                Write-Status "MCP $($server.Name): not installed (required)" 'Warning'
            } else {
                Write-Status "MCP $($server.Name): not installed (optional)" 'Dim'
            }
        }
    }
}

function Show-SkillsStatus {
    Write-Section "Skills Status"

    $skillsDir = "C:\project\vision\.github\skills"
    if (Test-Path $skillsDir) {
        $skills = Get-ChildItem -Path $skillsDir -Directory -ErrorAction SilentlyContinue
        Write-Status "Skills directory: $($skills.Count) skills available" 'Success'

        $eliteSkills = @(
            "vision-runtime-ops",
            "vision-debugging",
            "vision-tool-dev",
            "vision-code-review",
            "vision-mcp-tools",
            "vision-web-research",
            "vision-context-brain",
            "openclaw-getting-started",
            "archon"
        )

        foreach ($skill in $eliteSkills) {
            $skillPath = Join-Path $skillsDir $skill
            if (Test-Path $skillPath) {
                Write-Status "  ✓ $skill" 'Success'
            } else {
                Write-Status "  ✗ $skill" 'Dim'
            }
        }
    } else {
        Write-Status "Skills directory not found" 'Warning'
    }
}

function Install-McpServer($Name) {
    Write-Status "Installing MCP server: $Name..." 'Info'
    try {
        npx -y "@modelcontextprotocol/server-$Name" --version 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "MCP $Name installed successfully" 'Success'
            return $true
        }
    } catch {
        Write-Status "Failed to install MCP $Name`: $_" 'Error'
    }
    return $false
}

function Invoke-EliteToolsMenu {
    while ($true) {
        Clear-Host
        Show-Banner
        Write-Host ""
        Write-Host "  ELITE TOOLS MENU" -ForegroundColor $Colors.Accent
        Write-Host ""
        Write-Host "  [1] Check MCP Servers Status" -ForegroundColor $Colors.Info
        Write-Host "  [2] Check Skills Status" -ForegroundColor $Colors.Info
        Write-Host "  [3] Show Full Diagnostics" -ForegroundColor $Colors.Info
        Write-Host "  [4] Configure OpenClaw Elite" -ForegroundColor $Colors.Info
        Write-Host "  [5] Launch Copilot (Default)" -ForegroundColor $Colors.Info
        Write-Host "  [6] Launch Copilot (Power Model)" -ForegroundColor $Colors.Info
        Write-Host "  [B] Back to Main Menu" -ForegroundColor $Colors.Dim
        Write-Host "  [Q] Quit" -ForegroundColor $Colors.Dim
        Write-Host ""

        $choice = Read-Host "Select option"

        switch ($choice) {
            '1' { Show-McpStatus; Read-Host "`nPress Enter to continue" }
            '2' { Show-SkillsStatus; Read-Host "`nPress Enter to continue" }
            '3' { Show-Diagnostics; Read-Host "`nPress Enter to continue" }
            '4' {
                if (Test-Path "C:\project\vision\openclaw-elite-installer.ps1") {
                    & "C:\project\vision\openclaw-elite-installer.ps1" -ConfigureOpenClaw
                } else {
                    Write-Status "Installer not found" 'Error'
                }
                Read-Host "`nPress Enter to continue"
            }
            '5' { Invoke-OpenClawCLI -SelectedModel 'default'; return }
            '6' { Invoke-OpenClawCLI -SelectedModel 'power'; return }
            'b' { return }
            'B' { return }
            'q' { exit 0 }
            'Q' { exit 0 }
        }
    }
}
if ($Help) {
    Show-Help
    return
}

if ($Interactive) {
    Show-InteractiveMenu
    return
}

if ($Status) {
    Show-Banner
    Show-Status
    exit 0
}

if ($Config) {
    Show-Banner
    Show-Config
    exit 0
}

if ($Fix) {
    Show-Banner
    Invoke-Fix
    exit 0
}

Show-Banner

if ($Diagnostics) {
    Show-Diagnostics
    exit 0
}

if ($VisionCheck) {
    Write-Section "Vision Backend Check"
    $visionTest = Test-VisionBackend
    if ($visionTest.Success) {
        Write-Status "Vision backend is healthy" 'Success'
        $visionTest.Response | ConvertTo-Json -Depth 3 | Write-Host
    } else {
        Write-Status "Vision backend check failed: $($visionTest.Error)" 'Error'
        exit 1
    }
    exit 0
}

if ($Verify) {
    Write-Section "OpenClaw API Verification"

    $config = Get-OpenClawConfig
    if (-not $config) {
        Write-Status "OpenClaw config not found" 'Error'
        exit 1
    }

    $apiTest = Test-OpenClawGateway -Config $config
    if ($apiTest.Success) {
        Write-Status "OpenClaw API OK ($($apiTest.StatusCode))" 'Success'
        Write-Host ""
        Write-Host "Available Models:" -ForegroundColor $Colors.Accent
        $apiTest.Response.data | ForEach-Object {
            Write-Host "  • $($_.id)" -ForegroundColor $Colors.Info
        }
        exit 0
    } else {
        Write-Status "OpenClaw API check failed: $($apiTest.Error)" 'Error'
        Write-Status "Gateway may not be running. Try: openclaw gateway run" 'Warning'
        exit 1
    }
}

# Default: Launch Copilot CLI
if (-not $Quick) {
    $config = Get-OpenClawConfig
    if ($config) {
        $apiTest = Test-OpenClawGateway -Config $config
        if (-not $apiTest.Success) {
            Write-Status "OpenClaw gateway not responding" 'Error'
            Write-Status "Attempting to start gateway..." 'Warning'
            $openClawCommand = Get-Command 'openclaw' -ErrorAction SilentlyContinue
            if ($openClawCommand) {
                Start-Process -FilePath $openClawCommand.Source -ArgumentList @('gateway', 'run') | Out-Null
            } else {
                Write-Status 'OpenClaw CLI not found; cannot auto-start gateway.' 'Error'
            }
            Start-Sleep -Seconds 3
        }
    }
}

# Log session if name provided
if ($SessionName) {
    Write-SessionLog -Model $Model -SessionName $SessionName
}

Invoke-OpenClawCLI -SelectedModel $Model
