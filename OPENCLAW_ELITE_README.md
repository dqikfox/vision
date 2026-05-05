# 🦞 OpenClaw Elite Dev Environment

An enhanced OpenClaw integration for Vision with **12 MCP servers**, **25+ skills**, **full phone control**, diagnostics, multiple model support, interactive menu, and VS Code task integration.

## Elite Features

### MCP Servers (12 Total)
- ✅ **filesystem** - Read/write files in the vision project
- ✅ **github** - GitHub API for issues, PRs, code search
- ✅ **memory** - Persistent knowledge graph memory across sessions
- ✅ **sequential-thinking** - Structured multi-step reasoning
- ✅ **brave-search** - Web search via Brave Search API
- ✅ **fetch** - Fetch web pages and extract content
- ✅ **sqlite** - SQLite database for persistent storage
- ✅ **postgres** - PostgreSQL database access
- ✅ **redis** - Redis cache and data store
- ✅ **puppeteer** - Browser automation via Puppeteer
- ✅ **pdf** - Read and extract text from PDF files
- ✅ **everything** - Combined search, fetch, and filesystem tools

### Phone Control 📱 (NEW!)
Full Android phone control via ADB:
- ✅ **Screenshot** - Take screenshots and save to PC
- ✅ **Tap/Swipe** - Touch input at coordinates
- ✅ **Text Input** - Type text on phone
- ✅ **Key Presses** - HOME, BACK, POWER, VOLUME, etc.
- ✅ **App Launch** - Launch any installed app
- ✅ **App List** - View all installed apps
- ✅ **Screen Mirror** - Mirror phone to PC (requires scrcpy)
- ✅ **WiFi ADB** - Connect wirelessly
- ✅ **Interactive Menu** - Full control interface

### Skills (25+ Available)
- ✅ **vision-runtime-ops** - Runtime operations for Vision
- ✅ **vision-debugging** - Debug runtime, voice, WebSocket issues
- ✅ **vision-tool-dev** - Add new tools to Vision
- ✅ **vision-code-review** - Full code review capabilities
- ✅ **vision-type-safety** - Fix mypy and type errors
- ✅ **vision-home-ops** - Home PC/network/security tasks
- ✅ **vision-documentation-ops** - Documentation management
- ✅ **vision-mcp-builder** - Add MCP capabilities
- ✅ **vision-mcp-tools** - Master MCP servers
- ✅ **vision-web-research** - Web search and research
- ✅ **vision-context-ops** - Improve Copilot context
- ✅ **vision-context-brain** - Machine-readable context brain
- ✅ **vision-cognitive-council** - Multi-perspective reasoning
- ✅ **vision-performance** - Profile and optimize performance
- ✅ **vision-git-ops** - Git workflow management
- ✅ **vision-multi-monitor** - Multi-monitor support
- ✅ **openclaw-getting-started** - OpenClaw setup and onboarding
- ✅ **archon** - AI workflow automation
- ✅ **apex-brain** - Enhanced reasoning with Tree-of-Thoughts
- ✅ **bug-triage** - Reproduce and isolate defects
- ✅ **memory-ops** - Persistent cross-session memory
- ✅ **release-readiness** - Prepare changes for merge
- ✅ **repo-onboarding** - Understand unfamiliar repositories
- ✅ **task-decomposition** - Break requests into steps
- ✅ **tool-routing** - Choose the right tool for the job
- ✅ **web-debugging** - Investigate website problems

### Core Features
- ✅ **Full Diagnostics** - Check OpenClaw, Vision backend, MCP servers, and system health
- ✅ **Multiple Models** - Switch between default, fast (GPT-4o-mini), power (Claude), and local models
- ✅ **Interactive Menu** - Easy-to-use interactive mode with all options
- ✅ **Quick Status** - One-command status overview of all components
- ✅ **Vision Integration** - Verify Vision backend health before launching
- ✅ **VS Code Tasks** - One-click launch from VS Code task runner
- ✅ **Batch Menu** - Interactive menu for non-PowerShell users
- ✅ **Auto-Start Gateway** - Automatically starts OpenClaw gateway if not running
- ✅ **Session Logging** - Track your Copilot sessions with named sessions
- ✅ **Config Management** - View and fix OpenClaw configuration issues
- ✅ **MCP Status** - Check which MCP servers are installed and running
- ✅ **Skills Registry** - View available skills and their status

## Quick Start

### Option 1: Interactive Mode (Recommended)
```powershell
.\openclaw-elite.ps1 -Interactive
```

### Option 2: Phone Control
```powershell
# Interactive phone control menu
.\openclaw-elite-phone.ps1 -Interactive

# Quick screenshot
.\openclaw-elite-phone.ps1 -Screenshot

# Check phone status
.\openclaw-elite-phone.ps1 -Status

# Connect via WiFi
.\openclaw-elite-phone.ps1 -ConnectWiFi -IpAddress 192.168.1.100
```

### Option 3: Install Everything
```powershell
# Install all MCP servers, skills, and configure OpenClaw
.\openclaw-elite-installer.ps1 -All

# Or dry run to see what would be installed
.\openclaw-elite-installer.ps1 -All -DryRun
```

### Option 4: Interactive Batch Menu
```batch
openclaw-elite.bat
```

### Option 5: PowerShell Direct
```powershell
# Quick status check
.\openclaw-elite.ps1 -Status

# Launch with default model
.\openclaw-elite.ps1

# Launch with specific model and session name
.\openclaw-elite.ps1 -Model power -SessionName "CodeReview"

# Run full diagnostics
.\openclaw-elite.ps1 -Diagnostics

# Show current configuration
.\openclaw-elite.ps1 -Config

# Fix config issues
.\openclaw-elite.ps1 -Fix

# Verify OpenClaw API only
.\openclaw-elite.ps1 -Verify

# Check Vision backend health
.\openclaw-elite.ps1 -VisionCheck

# Quick launch (skip all checks)
.\openclaw-elite.ps1 -Quick
```

### Option 6: VS Code Tasks
Open VS Code Command Palette (`Ctrl+Shift+P`) and run:
- `Tasks: Run Task` → `OpenClaw Elite: Interactive Menu`
- `Tasks: Run Task` → `OpenClaw Elite: Phone Control`
- `Tasks: Run Task` → `OpenClaw Elite: Phone Screenshot`
- `Tasks: Run Task` → `OpenClaw Elite: Phone Status`
- `Tasks: Run Task` → `OpenClaw Elite: Launch (Default)`
- `Tasks: Run Task` → `OpenClaw Elite: Launch (Fast Model)`
- `Tasks: Run Task` → `OpenClaw Elite: Launch (Power Model)`
- `Tasks: Run Task` → `OpenClaw Elite: Diagnostics`
- `Tasks: Run Task` → `OpenClaw Elite: Quick Status`

## Configuration

### Elite Config (`openclaw-elite-config.json`)
```json
{
  "elite": {
    "models": {
      "default": "openclaw/default",
      "fast": "openclaw/gpt-4o-mini",
      "power": "openclaw/claude-sonnet-4",
      "local": "openclaw/ollama-local"
    },
    "cli": {
      "auto_verify": true,
      "auto_start_gateway": true,
      "timeout_seconds": 30
    }
  }
}
```

### Full Elite Config (`openclaw-elite-full.json`)
Contains complete MCP server definitions, permissions, skills registry, tools configuration, hooks, and context settings.

### Phone Config (`openclaw-elite-phone.json`)
Phone control settings including ADB path, default screenshot location, and WiFi ADB preferences.

## Available Models

| Model | Description | Use Case |
|-------|-------------|----------|
| `default` | OpenClaw default | General purpose |
| `fast` | GPT-4o-mini | Quick tasks, simple queries |
| `power` | Claude Sonnet 4 | Complex reasoning, code review |
| `local` | Ollama local | Offline, privacy-sensitive |

## Prerequisites

1. **OpenClaw installed**: `npm install -g openclaw@latest`
2. **OpenClaw onboarded**: `openclaw onboard --install-daemon`
3. **GitHub Copilot CLI**: `gh copilot install`
4. **Vision backend** (optional): Running on `http://localhost:8765`
5. **Node.js**: v22.14+ (v24 recommended)
6. **ADB** (for phone control): Android SDK platform-tools
7. **scrcpy** (optional): For screen mirroring

## Installation

### Step 1: Install OpenClaw (if not already installed)
```powershell
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

### Step 2: Run the Elite Installer
```powershell
.\openclaw-elite-installer.ps1 -All
```

This will:
- Install all MCP servers
- Configure skills registry
- Merge elite settings into OpenClaw config
- Create environment variables script

### Step 3: Set Environment Variables
Edit `openclaw-elite-env.ps1` and set your API keys:
```powershell
$env:BRAVE_API_KEY = "your-brave-api-key"
$env:GH_TOKEN = "your-github-token"
```

Then source it:
```powershell
. .\openclaw-elite-env.ps1
```

### Step 4: Setup Phone Control (Optional)
1. Enable Developer Options on your Android phone
2. Enable USB Debugging
3. Connect via USB and accept the debugging prompt
4. Install scrcpy for screen mirroring: `winget install Genymobile.scrcpy`

## Phone Control Usage

### Interactive Menu
```powershell
.\openclaw-elite-phone.ps1 -Interactive
```

Menu options:
- **1** Take Screenshot
- **2** Tap on Screen (enter coordinates)
- **3** Swipe on Screen (enter start/end coordinates)
- **4** Type Text
- **5** Press Key (HOME, BACK, POWER, VOLUME_UP, VOLUME_DOWN, MENU, ENTER)
- **6** Launch App (enter package name)
- **7** List Installed Apps
- **8** Screen Mirror (requires scrcpy)
- **9** Change Device (if multiple phones)
- **S** Show Device Status
- **W** Connect WiFi ADB

### Direct Commands
```powershell
# Screenshot
.\openclaw-elite-phone.ps1 -Screenshot
.\openclaw-elite-phone.ps1 -Screenshot -SavePath "C:\Users\You\Desktop\myphone.png"

# List devices
.\openclaw-elite-phone.ps1 -ListDevices

# Check status
.\openclaw-elite-phone.ps1 -Status

# Connect via WiFi (after initial USB setup)
.\openclaw-elite-phone.ps1 -ConnectWiFi -IpAddress 192.168.1.100

# Start screen mirror
.\openclaw-elite-phone.ps1 -Mirror
```

## Troubleshooting

### OpenClaw not found
```powershell
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

### Gateway not running
```powershell
openclaw gateway run
# Or install as service:
openclaw gateway install
```

### Copilot CLI not found
```powershell
gh copilot install
```

### Vision backend not responding
Ensure Vision backend is running:
```powershell
python live_chat_app.py
```

### Fix config issues
```powershell
.\openclaw-elite.ps1 -Fix
```

### MCP servers not installed
```powershell
# Check status
.\openclaw-elite.ps1 -Interactive
# Then select option 4 (Elite Tools) → 1 (Check MCP Servers Status)

# Or install manually
npx -y @modelcontextprotocol/server-filesystem
npx -y @modelcontextprotocol/server-github
# ... etc
```

### Phone Control Issues

#### ADB not found
```powershell
# Install Android SDK platform-tools
# Download from: https://developer.android.com/studio/releases/platform-tools
# Or via winget: winget install Google.PlatformTools

# Add to PATH
[System.Environment]::SetEnvironmentVariable(
  "PATH",
  [System.Environment]::GetEnvironmentVariable("PATH","User") + ";C:\Users\$env:USERNAME\AppData\Local\Android\Sdk\platform-tools",
  "User"
)
```

#### Device unauthorized
1. Disconnect and reconnect USB cable
2. Check phone for "Allow USB debugging?" prompt
3. Tap "Allow"
4. Run: `adb devices` to verify

#### WiFi ADB not connecting
1. First connect via USB: `adb tcpip 5555`
2. Disconnect USB
3. Find phone IP: Settings → About Phone → Status → IP Address
4. Connect: `adb connect 192.168.1.xxx:5555`

## Files

| File | Purpose |
|------|---------|
| `openclaw-elite.ps1` | Main PowerShell launcher with all features |
| `openclaw-elite.bat` | Batch wrapper with interactive menu |
| `openclaw-elite-config.json` | Basic configuration for models and settings |
| `openclaw-elite-full.json` | Complete elite configuration with MCP, skills, tools |
| `openclaw-elite-installer.ps1` | Installer for MCP servers and configuration |
| `openclaw-elite-env.ps1` | Environment variables script (created by installer) |
| `openclaw-elite-phone.ps1` | Phone control script (NEW!) |
| `openclaw-elite-phone.json` | Phone control configuration (NEW!) |
| `.vscode/tasks.json` | VS Code task definitions |
| `create-openclaw-elite-shortcut.ps1` | Creates desktop shortcut |

## Integration with Vision

The elite launcher can check Vision backend health before launching Copilot CLI. This ensures your local AI tools are ready.

To enable Vision checks:
1. Ensure Vision backend is running: `python live_chat_app.py`
2. Run launcher with Vision check: `.\openclaw-elite.ps1 -VisionCheck`

## Session Logging

Track your Copilot sessions with named sessions:
```powershell
.\openclaw-elite.ps1 -Model power -SessionName "RefactoringTask"
```

Sessions are logged to `~/.openclaw/elite-sessions.log`

## Elite Tools Menu

Access the Elite Tools Menu from the interactive mode (option 4) to:
- Check MCP servers status
- Check skills status
- View full diagnostics
- Configure OpenClaw Elite
- Launch Copilot with different models

## Phone Control Menu

Access the Phone Control from the interactive mode (option 5) or directly via:
```powershell
.\openclaw-elite-phone.ps1 -Interactive
```

## License

Part of the Vision project. See main LICENSE file.
