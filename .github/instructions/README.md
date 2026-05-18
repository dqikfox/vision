# GitHub Copilot Custom Instructions - Setup Guide

## What Are Custom Instructions?

Custom instruction files allow you to provide **file-specific guidance** to GitHub Copilot. When you work on a file, Copilot automatically loads instructions that match that file's path pattern, making it project-aware and consistent.

---

## ✅ Enable the Feature (Visual Studio 2022)

1. Open **Visual Studio 2022**
2. Go to **Tools > Options**
3. Navigate to **GitHub > Copilot > Copilot Chat**
4. Check: **"Enable custom instructions to be loaded from .github/instructions/*.instructions.md files and added to requests"**
5. Click **OK**

---

## 📁 Vision Project Instructions

We've created **6 targeted instruction files** for the Vision project:

### 1. `python-backend.instructions.md`
**Applies to**: `vision_*.py` files

**Teaches Copilot**:
- Modern Python standards (`from __future__ import annotations`)
- Error handling patterns (specific exceptions + logging)
- Configuration management (environment variables only)
- WebSocket message structure
- MCP tool patterns
- Accessibility considerations

### 2. `mcp-server.instructions.md`
**Applies to**: `vision_mcp_server.py`

**Teaches Copilot**:
- MCP server architecture (thin wrapper pattern)
- Tool function structure
- Response normalization
- Screenshot handling and sanitization
- Environment variable usage
- Error message guidelines

### 3. `voice-overlay.instructions.md`
**Applies to**: `voice_overlay.py`

**Teaches Copilot**:
- Tkinter GUI design philosophy
- Modern color palette usage
- UI component guidelines (header, labels, VU meter, buttons)
- WebSocket communication patterns
- Threading best practices
- Window management and drag-and-drop

### 4. `html-webui.instructions.md`
**Applies to**: `**/*.html` (all HTML files)

**Teaches Copilot**:
- Futuristic dark theme design philosophy
- Color palette consistency
- Typography standards (Orbitron, Share Tech Mono)
- Accessibility requirements (WCAG AA, keyboard nav, screen reader)
- WebSocket integration patterns
- Visual effects (scan lines, glows)
- Mobile responsiveness

### 5. `powershell-scripts.instructions.md`
**Applies to**: `**/*.ps1` (all PowerShell files)

**Teaches Copilot**:
- PowerShell best practices (approved verbs, PascalCase)
- Error handling patterns
- Vision-specific patterns (port checking, health checks)
- Ollama management
- Configuration loading
- Browser automation
- Cleanup and exit handling

### 6. `rag-system.instructions.md`
**Applies to**: `vision_rag*.py` files

**Teaches Copilot**:
- RAG architecture (SQLite FTS5)
- Indexing patterns
- Search API usage
- FTS5 query syntax
- Chunking strategy
- Database schema
- LLM integration
- Performance optimization

---

## 🎯 How It Works

When you open a file in Visual Studio, Copilot:

1. **Checks file path** against all instruction files' `applyTo` patterns
2. **Loads matching instructions** automatically
3. **Applies them to responses** when you ask questions or request code
4. **Shows references** in the response card (click to see which instructions were used)

### Example Workflow

```
You open: voice_overlay.py
Copilot loads: voice-overlay.instructions.md + python-backend.instructions.md
You ask: "Add a new button to toggle voice provider"
Copilot responds: Uses modern color palette (BLUE_BRIGHT, SURFACE_LIGHT),
                  adds cursor="hand2", creates button with proper spacing,
                  includes WebSocket message handling
```

---

## 🧪 Test the Instructions

### Test 1: Python Backend
1. Open `vision_mcp_server.py`
2. Ask Copilot: **"Create a new tool to check microphone status"**
3. **Expected**: Should use `@mcp.tool()`, return `dict[str, Any]` with `ok` field, include error handling

### Test 2: GUI (Tkinter)
1. Open `voice_overlay.py`
2. Ask Copilot: **"Add a status indicator for WiFi connection"**
3. **Expected**: Should use modern color palette (`BLUE_BRIGHT`, `GREEN_BRIGHT`, etc.), add to HUD frame, use 8pt font

### Test 3: Web UI
1. Open `live_chat_ui_v3.html`
2. Ask Copilot: **"Create a settings panel with accessibility controls"**
3. **Expected**: Should use Orbitron font, `:root` CSS variables, WCAG AA contrast, keyboard navigation

### Test 4: PowerShell
1. Open `vision_master_launcher.ps1`
2. Ask Copilot: **"Add a function to restart the Vision backend"**
3. **Expected**: Should use PascalCase (`Restart-VisionBackend`), include error handling, perform health checks

### Test 5: RAG System
1. Open `vision_rag.py`
2. Ask Copilot: **"Add a method to export search results as CSV"**
3. **Expected**: Should follow RAG patterns, use SQLite FTS5, include chunking logic

---

## 🔍 View Active Instructions

When Copilot responds:
1. Look for the **references section** in the response card
2. Click on any reference to see the instruction content
3. Verify the right instructions were loaded

---

## ✏️ Customize Instructions

### Adding New Instructions
1. Create file: `.github/instructions/your-topic.instructions.md`
2. Add header with glob pattern:
   ```markdown
   ---
   applyTo: "path/pattern/**/*.ext"
   ---
   ```
3. Write natural language instructions
4. Save and test

### Editing Existing Instructions
1. Open `.github/instructions/*.instructions.md` file
2. Edit in natural language (Copilot understands it!)
3. Save - changes apply immediately
4. Test with Copilot

### Composing Instructions
Reference other instruction files:
```markdown
---
applyTo: "tests/**/*.py"
---

# Test Instructions

Follow all guidelines from `python-backend.instructions.md` plus:
- Use pytest fixtures
- Mock external services
- Test accessibility features
```

---

## 📊 Instruction Files Summary

| File | Applies To | Lines | Key Topics |
|------|-----------|-------|------------|
| `python-backend.instructions.md` | `vision_*.py` | 150+ | Imports, errors, config, WebSocket, MCP, accessibility |
| `mcp-server.instructions.md` | `vision_mcp_server.py` | 200+ | MCP architecture, tools, responses, screenshots |
| `voice-overlay.instructions.md` | `voice_overlay.py` | 300+ | Tkinter GUI, colors, components, WebSocket, threading |
| `html-webui.instructions.md` | `**/*.html` | 250+ | Dark theme, typography, accessibility, WebSocket, effects |
| `powershell-scripts.instructions.md` | `**/*.ps1` | 300+ | PowerShell standards, Vision patterns, error handling |
| `rag-system.instructions.md` | `vision_rag*.py` | 250+ | SQLite FTS5, indexing, search, LLM integration |

**Total**: 1,450+ lines of targeted instructions

---

## 🎉 Benefits

### Before Custom Instructions
- Copilot uses generic Python/JavaScript/HTML patterns
- Inconsistent code style across Vision project
- Manual corrections needed for Vision-specific patterns
- No knowledge of Vision architecture or conventions

### After Custom Instructions
- ✅ **Project-aware**: Knows Vision architecture, patterns, standards
- ✅ **Consistent**: Follows Vision color palette, naming, error handling
- ✅ **Accessible**: Suggests WCAG-compliant, keyboard-friendly code
- ✅ **Fast**: No need to explain Vision conventions every time
- ✅ **Accurate**: Uses correct environment variables, message types, API patterns

---

## 🚀 Next Steps

1. ✅ **Enable feature** in Visual Studio 2022 (see instructions above)
2. ✅ **Test instructions** with 5 test prompts
3. ✅ **Review references** in Copilot responses to verify loading
4. ✅ **Customize** instructions for your specific needs
5. ✅ **Share** with team (instructions are committed to repo)

---

## 📚 Resources

- [GitHub Copilot Custom Instructions Docs](https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- Vision instruction files: `.github/instructions/*.instructions.md`
- Vision coding standards: `CONTRIBUTING.md`
- Project architecture: `README.md`

---

**Status**: ✅ Custom instructions configured for Vision project  
**Impact**: Copilot is now fully project-aware and context-sensitive  
**Team benefit**: Consistent code generation across all Vision files

---

*Generated by ULTRON via GitHub Copilot - Vision Maintainer Agent*
