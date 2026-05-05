# OpenClaw Elite Memory & Self-Awareness System
# Provides persistent memory, context awareness, and self-monitoring

param(
    [switch]$Initialize,
    [switch]$ShowStatus,
    [switch]$ShowMemory,
    [switch]$ClearMemory,
    [switch]$ExportMemory,
    [string]$ImportPath = "",
    [switch]$SelfAwareness,
    [switch]$Learn,
    [string]$AddFact = "",
    [string]$Category = "general",
    [switch]$Help
)

$script:Version = "1.0.0"
$script:MemoryPath = "$env:USERPROFILE\.openclaw\elite-memory.json"
$script:ContextPath = "$env:USERPROFILE\.openclaw\elite-context.json"
$script:SelfPath = "$env:USERPROFILE\.openclaw\elite-self.json"
$script:LearningPath = "$env:USERPROFILE\.openclaw\elite-learning.json"
$script:SessionPath = "$env:USERPROFILE\.openclaw\elite-sessions.json"

$Colors = @{
    Success = 'Green'
    Info = 'Cyan'
    Warning = 'Yellow'
    Error = 'Red'
    Accent = 'Magenta'
    Memory = 'DarkCyan'
    Self = 'DarkYellow'
}

function Write-Status($Message, $Type = 'Info') {
    $color = $Colors[$Type]
    $prefix = switch ($Type) {
        'Success' { '✓' }
        'Error' { '✗' }
        'Warning' { '⚠' }
        'Memory' { '🧠' }
        'Self' { '🤖' }
        default { '→' }
    }
    Write-Host "$prefix $Message" -ForegroundColor $color
}

function Show-Banner {
    Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║     🧠 OpenClaw Elite Memory & Self-Awareness v$script:Version       ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $Colors.Memory
}

function Show-Help {
    @"
OpenClaw Elite Memory & Self-Awareness System

USAGE:
    .\openclaw-elite-memory.ps1 [OPTIONS]

OPTIONS:
    -Initialize          Initialize memory system
    -ShowStatus          Show system status
    -ShowMemory          Display current memory
    -ClearMemory         Clear all memory (with backup)
    -ExportMemory        Export memory to file
    -ImportPath <path>  Import memory from file
    -SelfAwareness       Run self-awareness check
    -Learn               Process learning queue
    -AddFact <fact>      Add a fact to memory
    -Category <cat>      Category for new fact
    -Help                Show this help

EXAMPLES:
    .\openclaw-elite-memory.ps1 -Initialize
    .\openclaw-elite-memory.ps1 -ShowMemory
    .\openclaw-elite-memory.ps1 -AddFact "User prefers dark mode" -Category "preferences"
    .\openclaw-elite-memory.ps1 -SelfAwareness
"@ | Write-Host
}

# ── Memory Management ────────────────────────────────────────────────────────

function Initialize-MemorySystem {
    Write-Status "Initializing memory system..." 'Memory'

    $memoryDir = "$env:USERPROFILE\.openclaw"
    if (-not (Test-Path $memoryDir)) {
        New-Item -ItemType Directory -Path $memoryDir -Force | Out-Null
    }

    # Initialize memory structure
    $memory = @{
        version = $script:Version
        created = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        facts = @()
        preferences = @{}
        patterns = @()
        sessions = @()
        context = @{}
        self = @{
            identity = "OpenClaw Elite"
            version = $script:Version
            capabilities = @(
                "code-generation",
                "debugging",
                "analysis",
                "learning",
                "memory-management",
                "phone-control",
                "mcp-tools"
            )
            limitations = @(
                "no-internet-access",
                "file-system-only",
                "user-supervised"
            )
            goals = @(
                "assist-user",
                "learn-patterns",
                "improve-over-time"
            )
        }
    }

    Save-Memory $memory
    Write-Status "Memory system initialized" 'Success'

    # Initialize context
    $context = @{
        currentSession = @{
            startTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            workingDirectory = $PWD.Path
            gitBranch = $(git branch --show-current 2>$null || "unknown")
            environment = @{
                os = $env:OS
                powershellVersion = $PSVersionTable.PSVersion.ToString()
                user = $env:USERNAME
            }
        }
        history = @()
        activeTasks = @()
        completedTasks = @()
    }

    Save-Context $context
    Write-Status "Context system initialized" 'Success'

    # Initialize learning
    $learning = @{
        patterns = @()
        corrections = @()
        improvements = @()
        lastLearning = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }

    Save-Learning $learning
    Write-Status "Learning system initialized" 'Success'
}

function Get-Memory {
    if (Test-Path $script:MemoryPath) {
        return Get-Content $script:MemoryPath | ConvertFrom-Json
    }
    return $null
}

function Save-Memory($Memory) {
    $Memory | ConvertTo-Json -Depth 10 | Set-Content $script:MemoryPath
}

function Get-Context {
    if (Test-Path $script:ContextPath) {
        return Get-Content $script:ContextPath | ConvertFrom-Json
    }
    return $null
}

function Save-Context($Context) {
    $Context | ConvertTo-Json -Depth 10 | Set-Content $script:ContextPath
}

function Get-Learning {
    if (Test-Path $script:LearningPath) {
        return Get-Content $script:LearningPath | ConvertFrom-Json
    }
    return $null
}

function Save-Learning($Learning) {
    $Learning | ConvertTo-Json -Depth 10 | Set-Content $script:LearningPath
}

# ── Self-Awareness Functions ─────────────────────────────────────────────────

function Show-SelfAwareness {
    Write-Status "Running self-awareness check..." 'Self'

    $memory = Get-Memory
    if (-not $memory) {
        Write-Status "Memory not initialized. Run -Initialize first." 'Error'
        return
    }

    Write-Host ""
    Write-Host "── Self Identity ──" -ForegroundColor $Colors.Accent
    Write-Status "Name: $($memory.self.identity)" 'Self'
    Write-Status "Version: $($memory.self.version)" 'Self'
    Write-Status "Memory Version: $($memory.version)" 'Self'

    Write-Host ""
    Write-Host "── Capabilities ──" -ForegroundColor $Colors.Accent
    foreach ($cap in $memory.self.capabilities) {
        Write-Status "  ✓ $cap" 'Success'
    }

    Write-Host ""
    Write-Host "── Limitations ──" -ForegroundColor $Colors.Accent
    foreach ($lim in $memory.self.limitations) {
        Write-Status "  ⚠ $lim" 'Warning'
    }

    Write-Host ""
    Write-Host "── Goals ──" -ForegroundColor $Colors.Accent
    foreach ($goal in $memory.self.goals) {
        Write-Status "  → $goal" 'Info'
    }

    Write-Host ""
    Write-Host "── Memory Statistics ──" -ForegroundColor $Colors.Accent
    Write-Status "Facts stored: $($memory.facts.Count)" 'Memory'
    Write-Status "Preferences: $($memory.preferences.Count)" 'Memory'
    Write-Status "Patterns learned: $($memory.patterns.Count)" 'Memory'
    Write-Status "Sessions tracked: $($memory.sessions.Count)" 'Memory'

    # Context awareness
    $context = Get-Context
    if ($context) {
        Write-Host ""
        Write-Host "── Current Context ──" -ForegroundColor $Colors.Accent
        Write-Status "Working directory: $($context.currentSession.workingDirectory)" 'Info'
        Write-Status "Git branch: $($context.currentSession.gitBranch)" 'Info'
        Write-Status "Session started: $($context.currentSession.startTime)" 'Info'
        Write-Status "Active tasks: $($context.activeTasks.Count)" 'Info'
        Write-Status "Completed tasks: $($context.completedTasks.Count)" 'Info'
    }

    # Learning status
    $learning = Get-Learning
    if ($learning) {
        Write-Host ""
        Write-Host "── Learning Status ──" -ForegroundColor $Colors.Accent
        Write-Status "Patterns learned: $($learning.patterns.Count)" 'Memory'
        Write-Status "Corrections made: $($learning.corrections.Count)" 'Memory'
        Write-Status "Improvements: $($learning.improvements.Count)" 'Memory'
        Write-Status "Last learning: $($learning.lastLearning)" 'Memory'
    }
}

function Add-MemoryFact($Fact, $Category) {
    $memory = Get-Memory
    if (-not $memory) {
        Write-Status "Memory not initialized. Run -Initialize first." 'Error'
        return
    }

    $factObj = @{
        id = [Guid]::NewGuid().ToString()
        content = $Fact
        category = $Category
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        accessCount = 0
        lastAccessed = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }

    $memory.facts += $factObj
    Save-Memory $memory

    Write-Status "Fact added to memory: $Fact" 'Memory'
}

function Show-MemoryContents {
    $memory = Get-Memory
    if (-not $memory) {
        Write-Status "Memory not initialized" 'Warning'
        return
    }

    Write-Host ""
    Write-Host "── Memory Contents ──" -ForegroundColor $Colors.Accent

    if ($memory.facts.Count -eq 0) {
        Write-Status "No facts in memory" 'Warning'
    } else {
        Write-Status "Facts ($($memory.facts.Count)):" 'Memory'
        foreach ($fact in $memory.facts | Select-Object -Last 10) {
            Write-Host "  [$($fact.category)] $($fact.content)" -ForegroundColor $Colors.Dim
        }
        if ($memory.facts.Count -gt 10) {
            Write-Host "  ... and $($memory.facts.Count - 10) more" -ForegroundColor $Colors.Dim
        }
    }

    if ($memory.preferences.Count -gt 0) {
        Write-Host ""
        Write-Status "Preferences:" 'Memory'
        $memory.preferences.PSObject.Properties | ForEach-Object {
            Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor $Colors.Dim
        }
    }

    if ($memory.patterns.Count -gt 0) {
        Write-Host ""
        Write-Status "Learned Patterns:" 'Memory'
        foreach ($pattern in $memory.patterns | Select-Object -Last 5) {
            Write-Host "  • $($pattern.description)" -ForegroundColor $Colors.Dim
        }
    }
}

function Export-MemoryData {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $exportPath = "$env:USERPROFILE\.openclaw\elite-memory-export-$timestamp.json"

    $export = @{
        memory = Get-Memory
        context = Get-Context
        learning = Get-Learning
        exported = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        version = $script:Version
    }

    $export | ConvertTo-Json -Depth 10 | Set-Content $exportPath
    Write-Status "Memory exported to: $exportPath" 'Success'
    return $exportPath
}

function Import-MemoryData($Path) {
    if (-not (Test-Path $Path)) {
        Write-Status "Import file not found: $Path" 'Error'
        return
    }

    $import = Get-Content $Path | ConvertFrom-Json

    if ($import.memory) {
        Save-Memory $import.memory
        Write-Status "Memory imported" 'Success'
    }

    if ($import.context) {
        Save-Context $import.context
        Write-Status "Context imported" 'Success'
    }

    if ($import.learning) {
        Save-Learning $import.learning
        Write-Status "Learning data imported" 'Success'
    }
}

function Clear-MemoryData {
    # Backup first
    $backupPath = Export-MemoryData
    Write-Status "Memory backed up to: $backupPath" 'Info'

    # Clear files
    Remove-Item $script:MemoryPath -ErrorAction SilentlyContinue
    Remove-Item $script:ContextPath -ErrorAction SilentlyContinue
    Remove-Item $script:LearningPath -ErrorAction SilentlyContinue

    Write-Status "Memory cleared" 'Warning'
    Write-Status "Re-initialize with -Initialize to start fresh" 'Info'
}

function Process-Learning {
    $learning = Get-Learning
    if (-not $learning) {
        Write-Status "Learning system not initialized" 'Warning'
        return
    }

    Write-Status "Processing learning queue..." 'Memory'

    # Analyze patterns from sessions
    $memory = Get-Memory
    $context = Get-Context

    # Look for repeated commands
    $commandPatterns = @{}
    foreach ($session in $memory.sessions) {
        if ($session.commands) {
            foreach ($cmd in $session.commands) {
                if ($commandPatterns.ContainsKey($cmd)) {
                    $commandPatterns[$cmd]++
                } else {
                    $commandPatterns[$cmd] = 1
                }
            }
        }
    }

    # Identify frequent patterns
    $frequent = $commandPatterns.GetEnumerator() | Where-Object { $_.Value -gt 2 }
    foreach ($pattern in $frequent) {
        $patternObj = @{
            description = "Frequent command: $($pattern.Key)"
            frequency = $pattern.Value
            learned = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        $learning.patterns += $patternObj
        Write-Status "Learned pattern: $($pattern.Key) (used $($pattern.Value) times)" 'Memory'
    }

    $learning.lastLearning = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Save-Learning $learning

    Write-Status "Learning complete. Patterns learned: $($frequent.Count)" 'Success'
}

# ── Main Entry Point ─────────────────────────────────────────────────────────
if ($Help) {
    Show-Help
    exit 0
}

Show-Banner

if ($Initialize) {
    Initialize-MemorySystem
    exit 0
}

if ($ShowStatus) {
    Show-SelfAwareness
    exit 0
}

if ($ShowMemory) {
    Show-MemoryContents
    exit 0
}

if ($ClearMemory) {
    Clear-MemoryData
    exit 0
}

if ($ExportMemory) {
    Export-MemoryData
    exit 0
}

if ($ImportPath) {
    Import-MemoryData $ImportPath
    exit 0
}

if ($SelfAwareness) {
    Show-SelfAwareness
    exit 0
}

if ($Learn) {
    Process-Learning
    exit 0
}

if ($AddFact) {
    Add-MemoryFact $AddFact $Category
    exit 0
}

# Default: show status
Show-SelfAwareness
Write-Host ""
Write-Host "Use -Help for all options" -ForegroundColor $Colors.Dim
