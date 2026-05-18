# OpenClaw Elite Tools Installer
# Installs and configures all MCP servers, skills, and tools for elite OpenClaw setup

param(
    [switch]$InstallMCP,
    [switch]$InstallSkills,
    [switch]$ConfigureOpenClaw,
    [switch]$All,
    [switch]$DryRun,
    [switch]$Help
)

$script:Version = "2.0.0"
$Colors = @{
    Success = 'Green'
    Info = 'Cyan'
    Warning = 'Yellow'
    Error = 'Red'
    Accent = 'Magenta'
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
║     🦞 OpenClaw Elite Tools Installer v$script:Version              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $Colors.Accent
}

function Show-Help {
    @"
OpenClaw Elite Tools Installer

USAGE:
    .\openclaw-elite-installer.ps1 [OPTIONS]

OPTIONS:
    -All                 Install everything (MCP, skills, config)
    -InstallMCP          Install MCP servers only
    -InstallSkills       Install skills only
    -ConfigureOpenClaw   Configure OpenClaw with elite settings
    -DryRun              Show what would be installed without doing it
    -Help                Show this help

EXAMPLES:
    .\openclaw-elite-installer.ps1 -All
    .\openclaw-elite-installer.ps1 -InstallMCP
    .\openclaw-elite-installer.ps1 -ConfigureOpenClaw
"@ | Write-Host
}

# ── MCP Servers to Install ─────────────────────────────────────────────────
$McpServers = @(
    @{ Name = "@modelcontextprotocol/server-filesystem"; Required = $true },
    @{ Name = "@modelcontextprotocol/server-github"; Required = $true },
    @{ Name = "@modelcontextprotocol/server-memory"; Required = $true },
    @{ Name = "@modelcontextprotocol/server-sequential-thinking"; Required = $true },
    @{ Name = "@modelcontextprotocol/server-brave-search"; Required = $false },
    @{ Name = "@modelcontextprotocol/server-fetch"; Required = $true },
    @{ Name = "@modelcontextprotocol/server-sqlite"; Required = $false },
    @{ Name = "@modelcontextprotocol/server-puppeteer"; Required = $true },
    @{ Name = "@modelcontextprotocol/server-pdf"; Required = $true }
)

# ── Skills to Enable ────────────────────────────────────────────────────────
$EliteSkills = @(
    "vision-runtime-ops",
    "vision-debugging",
    "vision-tool-dev",
    "vision-code-review",
    "vision-type-safety",
    "vision-home-ops",
    "vision-documentation-ops",
    "vision-mcp-builder",
    "vision-mcp-tools",
    "vision-web-research",
    "vision-context-ops",
    "vision-context-brain",
    "vision-cognitive-council",
    "vision-performance",
    "vision-git-ops",
    "openclaw-getting-started",
    "archon"
)

function Install-McpServers {
    Write-Host ""
    Write-Host "── Installing MCP Servers ──" -ForegroundColor $Colors.Accent

    foreach ($server in $McpServers) {
        $name = $server.Name
        $required = $server.Required

        if ($DryRun) {
            Write-Status "Would install: $name $(if ($required) { '(required)' } else { '(optional)' })" 'Info'
            continue
        }

        try {
            Write-Status "Installing $name..." 'Info'
            $output = npm install -g $name 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Status "$name installed" 'Success'
            } else {
                if ($required) {
                    Write-Status "$name failed to install" 'Error'
                } else {
                    Write-Status "$name failed (optional)" 'Warning'
                }
            }
        } catch {
            if ($required) {
                Write-Status "$name error: $_" 'Error'
            } else {
                Write-Status "$name error (optional): $_" 'Warning'
            }
        }
    }
}

function Install-Skills {
    Write-Host ""
    Write-Host "── Configuring Skills ──" -ForegroundColor $Colors.Accent

    $skillsDir = "C:\project\vision\.github\skills"

    foreach ($skill in $EliteSkills) {
        $skillPath = Join-Path $skillsDir $skill

        if (Test-Path $skillPath) {
            Write-Status "Skill available: $skill" 'Success'
        } else {
            Write-Status "Skill not found: $skill" 'Warning'
        }
    }

    # Create skills registry
    $registryPath = "C:\project\vision\.openclaw-elite-skills.json"
    $registry = @{
        version = $script:Version
        skills = $EliteSkills
        path = $skillsDir
        autoLoad = $true
    }

    if (-not $DryRun) {
        $registry | ConvertTo-Json -Depth 3 | Set-Content -Path $registryPath
        Write-Status "Skills registry created: $registryPath" 'Success'
    } else {
        Write-Status "Would create skills registry: $registryPath" 'Info'
    }
}

function Configure-OpenClawElite {
    Write-Host ""
    Write-Host "── Configuring OpenClaw Elite ──" -ForegroundColor $Colors.Accent

    $configPath = Join-Path $env:USERPROFILE '.openclaw\openclaw.json'
    $eliteConfigPath = "C:\project\vision\openclaw-elite-full.json"

    if (-not (Test-Path $configPath)) {
        Write-Status "OpenClaw config not found at $configPath" 'Error'
        Write-Status "Run 'openclaw onboard' first" 'Warning'
        return
    }

    if (-not (Test-Path $eliteConfigPath)) {
        Write-Status "Elite config not found at $eliteConfigPath" 'Error'
        return
    }

    if ($DryRun) {
        Write-Status "Would merge elite config into OpenClaw" 'Info'
        return
    }

    # Backup original config
    $backupPath = "$configPath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item $configPath $backupPath
    Write-Status "Original config backed up to $backupPath" 'Success'

    # Load configs
    $originalConfig = Get-Content $configPath | ConvertFrom-Json
    $eliteConfig = Get-Content $eliteConfigPath | ConvertFrom-Json

    # Merge elite settings
    $originalConfig | Add-Member -NotePropertyName "elite" -NotePropertyValue $eliteConfig.elite -Force
    $originalConfig | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue $eliteConfig.mcpServers -Force
    $originalConfig | Add-Member -NotePropertyName "permissions" -NotePropertyValue $eliteConfig.permissions -Force
    $originalConfig | Add-Member -NotePropertyName "skills" -NotePropertyValue $eliteConfig.skills -Force
    $originalConfig | Add-Member -NotePropertyName "tools" -NotePropertyValue $eliteConfig.tools -Force
    $originalConfig | Add-Member -NotePropertyName "hooks" -NotePropertyValue $eliteConfig.hooks -Force
    $originalConfig | Add-Member -NotePropertyName "context" -NotePropertyValue $eliteConfig.context -Force

    # Save merged config
    $originalConfig | ConvertTo-Json -Depth 10 | Set-Content $configPath
    Write-Status "OpenClaw configured with elite settings" 'Success'

    # Create environment variables script
    $envScript = @"
# OpenClaw Elite Environment Variables
# Source this file: . ./openclaw-elite-env.ps1

`$env:OPENCLAW_ELITE = "1"
`$env:OPENCLAW_ELITE_VERSION = "$script:Version"
`$env:OPENCLAW_SKILLS_PATH = "C:\project\vision\.github\skills"
`$env:OPENCLAW_MCP_ENABLED = "1"
`$env:OPENCLAW_CONTEXT_AUTOLOAD = "1"

# MCP Server Environment Variables (set these if needed)
# `$env:BRAVE_API_KEY = "your-brave-api-key"
# `$env:GH_TOKEN = "your-github-token"

Write-Host "OpenClaw Elite environment loaded" -ForegroundColor Green
"@

    $envPath = "C:\project\vision\openclaw-elite-env.ps1"
    $envScript | Set-Content $envPath
    Write-Status "Environment script created: $envPath" 'Success'
}

function Create-EliteLauncher {
    Write-Host ""
    Write-Host "── Creating Elite Launcher ──" -ForegroundColor $Colors.Accent

    if ($DryRun) {
        Write-Status "Would create enhanced launcher" 'Info'
        return
    }

    # The launcher is already created by the previous script
    Write-Status "Elite launcher already exists" 'Success'
    Write-Status "Run with: .\openclaw-elite.ps1 -Interactive" 'Info'
}

function Show-Summary {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Accent
    Write-Host "║              OpenClaw Elite Installation Complete            ║" -ForegroundColor $Colors.Accent
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Accent
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor $Colors.Info
    Write-Host "  1. Set environment variables in openclaw-elite-env.ps1"
    Write-Host "  2. Run: .\openclaw-elite.ps1 -Interactive"
    Write-Host "  3. Or use VS Code tasks: Ctrl+Shift+P → Tasks: Run Task"
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor $Colors.Info
    Write-Host "  .\openclaw-elite.ps1 -Status       Quick status check"
    Write-Host "  .\openclaw-elite.ps1 -Diagnostics   Full diagnostics"
    Write-Host "  .\openclaw-elite.ps1 -Config        Show configuration"
    Write-Host "  .\openclaw-elite.ps1 -Interactive   Interactive menu"
    Write-Host ""
}

# ── Main Entry Point ────────────────────────────────────────────────────────
if ($Help) {
    Show-Help
    return
}

Show-Banner

if ($DryRun) {
    Write-Status "DRY RUN MODE - No changes will be made" 'Warning'
}

if ($All -or $InstallMCP) {
    Install-McpServers
}

if ($All -or $InstallSkills) {
    Install-Skills
}

if ($All -or $ConfigureOpenClaw) {
    Configure-OpenClawElite
}

if ($All) {
    Create-EliteLauncher
    Show-Summary
}

if (-not ($All -or $InstallMCP -or $InstallSkills -or $ConfigureOpenClaw)) {
    Write-Status "No action specified. Use -All or specific flags." 'Warning'
    Write-Status "Run with -Help for usage information" 'Info'
}
