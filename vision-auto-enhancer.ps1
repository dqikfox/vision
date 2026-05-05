# Vision Auto-Enhancer Launcher
# Easy access to the automated content enhancement system

param(
    [switch]$FullCycle,
    [switch]$Readme,
    [string]$Docs = "",
    [string]$Blog = "",
    [string]$Review = "",
    [switch]$Help
)

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
║     🚀 Vision Auto-Enhancer                                  ║
║     Multi-Agent Content Collaboration System                 ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $Colors.Accent
}

function Show-Help {
    @"
Vision Auto-Enhancer - Automated Content Enhancement

USAGE:
    .\vision-auto-enhancer.ps1 [OPTIONS]

OPTIONS:
    -FullCycle           Run complete enhancement cycle
    -Readme              Enhance README.md only
    -Docs <topic>       Generate documentation for topic
    -Blog <feature>     Create blog post about feature
    -Review <file>      Review code file
    -Help                Show this help

EXAMPLES:
    .\vision-auto-enhancer.ps1 -FullCycle
    .\vision-auto-enhancer.ps1 -Readme
    .\vision-auto-enhancer.ps1 -Docs "OpenClaw Elite"
    .\vision-auto-enhancer.ps1 -Blog "New Phone Control Feature"
    .\vision-auto-enhancer.ps1 -Review "openclaw-elite.ps1"
"@ | Write-Host
}

# ── Main ───────────────────────────────────────────────────────────────────

if ($Help) {
    Show-Help
    exit 0
}

Show-Banner

# Check Python and dependencies
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Status "Python not found in PATH" 'Error'
    exit 1
}

# Build arguments
$args = @()
if ($FullCycle) {
    $args += "--full-cycle"
    Write-Status "Running full enhancement cycle..." 'Info'
}
elseif ($Readme) {
    $args += "--readme"
    Write-Status "Enhancing README.md..." 'Info'
}
elseif ($Docs) {
    $args += "--docs", $Docs
    Write-Status "Generating documentation for: $Docs" 'Info'
}
elseif ($Blog) {
    $args += "--blog", $Blog
    Write-Status "Creating blog post for: $Blog" 'Info'
}
elseif ($Review) {
    $args += "--review", $Review
    Write-Status "Reviewing code file: $Review" 'Info'
}
else {
    $args += "--full-cycle"
    Write-Status "Running full enhancement cycle (default)..." 'Info'
}

# Run the enhancer
$scriptPath = Join-Path $PSScriptRoot "vision_auto_enhancer.py"
if (-not (Test-Path $scriptPath)) {
    Write-Status "Auto-enhancer script not found: $scriptPath" 'Error'
    exit 1
}

Write-Host ""
& python $scriptPath @args

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Status "Auto-enhancement complete!" 'Success'
} else {
    Write-Host ""
    Write-Status "Auto-enhancement failed" 'Error'
}
