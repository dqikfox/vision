# Vision Multi-Agent Writer-Reviewer Workflow
## Automated Content Collaboration System

## 🎯 Overview

A complete multi-agent workflow using Microsoft Agent Framework SDK that enables automated content creation and refinement through Writer-Reviewer collaboration, integrated with the Vision project for continuous enhancement.

## 📁 Project Structure

```
vision/
├── agent_workflow/                    # Multi-agent workflow package
│   ├── content_collaboration.py      # Core Writer-Reviewer implementation
│   ├── workflow.py                   # Entry points and HTTP server
│   ├── requirements.txt              # Dependencies
│   ├── .env.template                 # Environment configuration
│   ├── README.md                     # Workflow documentation
│   ├── outputs/                      # Generated content
│   └── .vscode/
│       └── launch.json               # Debug configurations
│
├── vision_auto_enhancer.py          # Vision integration layer
├── vision-auto-enhancer.ps1         # PowerShell launcher
│
└── .vscode/tasks.json               # VS Code tasks
```

## 🏗️ Architecture

### Multi-Agent Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Content Collaboration                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Request                                               │
│       ↓                                                     │
│  ┌──────────────┐                                          │
│  │    Writer    │ → Creates initial content                 │
│  │    Agent     │                                          │
│  └──────┬───────┘                                          │
│         ↓                                                   │
│  ┌──────────────┐                                          │
│  │   Reviewer   │ → Provides feedback                      │
│  │    Agent     │ → APPROVED?                              │
│  └──────┬───────┘    ↓ YES    ↓ NO                         │
│         │         Final    Revision                         │
│         │         Output      ↓                             │
│         └─────────────────────┘                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Vision Integration

```
┌─────────────────────────────────────────────────────────────┐
│                 Vision Auto-Enhancement                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   README    │  │ OpenClaw   │  │   Phone     │         │
│  │ Enhancement │  │   Elite    │  │   Control   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘               │
│                          ↓                                  │
│              ┌─────────────────────┐                        │
│              │  Writer-Reviewer   │                        │
│              │     Workflow       │                        │
│              └──────────┬──────────┘                        │
│                         ↓                                   │
│              ┌─────────────────────┐                        │
│              │  Enhanced Content   │                        │
│              │  (Documentation,    │                        │
│              │   Blog Posts, etc)  │                        │
│              └─────────────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd c:\project\vision\agent_workflow

# Requires Python 3.14+

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install runtime dependencies
python -m pip install -r requirements.txt

# Optional: install development extras
python -m pip install -e '.[dev]'
```

### 2. Configure Environment

```powershell
copy .env.template .env
notepad .env
```

Set your Foundry credentials:
```env
FOUNDRY_PROJECT_ENDPOINT=https://your-project.openai.azure.com/
FOUNDRY_MODEL_DEPLOYMENT_NAME=gpt-4o
```

### 3. Run the Workflow

#### Option A: Direct Execution
```powershell
# Run example collaboration
python agent_workflow/workflow.py
```

#### Option B: Vision Auto-Enhancer
```powershell
# Run full enhancement cycle
.\vision-auto-enhancer.ps1 -FullCycle

# Or enhance specific areas
.\vision-auto-enhancer.ps1 -Readme
.\vision-auto-enhancer.ps1 -Docs "OpenClaw Elite"
.\vision-auto-enhancer.ps1 -Blog "New Features"
```

#### Option C: VS Code Tasks
- `Ctrl+Shift+P` → `Tasks: Run Task`
- Select `Vision: Auto-Enhance (Full Cycle)`

## 🎨 Features

### Writer Agent
- ✅ Creates initial content based on requirements
- ✅ Adapts to different content types (docs, code, blog)
- ✅ Revises based on reviewer feedback
- ✅ Maintains technical accuracy

### Reviewer Agent
- ✅ Evaluates on 6 criteria (clarity, accuracy, completeness, etc.)
- ✅ Provides actionable feedback
- ✅ Suggests concrete improvements
- ✅ Determines approval status

### Vision Integration
- ✅ Auto-enhances README.md
- ✅ Generates documentation for features
- ✅ Creates blog posts
- ✅ Reviews code files
- ✅ Tracks enhancements in log

## 📊 Workflow Output

The workflow produces:

1. **Final Content** - Refined text after collaboration
2. **Review History** - All feedback and iterations
3. **Metadata** - Timestamps, approval status, statistics
4. **Enhancement Log** - JSON tracking of all enhancements

Example output structure:
```
outputs/
├── documentation-openclaw-elite-20260428-120000.md
├── blog-vision-update-20260428-120500.md
├── review-openclaw-elite-ps1-20260428-121000.md
└── enhancement_log.json
```

## 🔧 Configuration

### Workflow Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `max_iterations` | 3 | Max review cycles |
| `output_dir` | ./outputs | Where to save content |
| `content_type` | documentation | Type of content |
| `tone` | professional | Writing style |

### Content Types

| Type | Use Case |
|------|----------|
| `documentation` | Technical docs, guides |
| `code` | Code examples, tutorials |
| `blog` | Articles, announcements |
| `review` | Analysis, comparisons |

## 🐛 Debugging

### Check Logs First

Before attaching a debugger, inspect the primary diagnostic log:

```powershell
Get-Content chat_events.log -Tail 50
Select-String -Path chat_events.log -Pattern "ERROR|EXCEPTION"
```

This usually surfaces failures in `content_collaboration.py` or `agent_workflow/workflow.py` faster than stepping into the debugger.

### With VS Code

1. Open `agent_workflow` folder
2. Set breakpoints in `content_collaboration.py`
3. Press F5 → Select "Agent Dev CLI: Content Workflow"

### With AI Toolkit Agent Inspector

1. Start with debugpy:
   ```powershell
   python -m debugpy --listen 5678 --wait-for-client agent_workflow/workflow.py
   ```
2. Attach in VS Code
3. Open Agent Inspector

## 🔗 Integration Points

### With OpenClaw Elite
The workflow can be invoked from OpenClaw Elite to:
- Generate documentation for new features
- Create blog posts about releases
- Review code changes

### With Vision Memory System
The workflow stores:
- Generated content in memory
- User preferences for content style
- Patterns from successful collaborations

### With Phone Control
Future enhancement: Generate mobile-friendly documentation and test on actual devices.

## 📈 Usage Examples

### Generate Documentation
```python
from vision_auto_enhancer import VisionAutoEnhancer

enhancer = VisionAutoEnhancer()
result = await enhancer.enhance_documentation(
    topic="Phone Control System",
    source_file=Path("openclaw-elite-phone.ps1")
)
```

### Create Blog Post
```python
result = await enhancer.create_blog_post(
    feature="Memory and Self-Awareness",
    highlights=[
        "Persistent memory across sessions",
        "Self-awareness capabilities",
        "Learning from interactions"
    ]
)
```

### Review Code
```python
result = await enhancer.generate_code_review(
    code_file=Path("openclaw-elite.ps1"),
    review_focus=["Security", "Performance", "Maintainability"]
)
```

## 🎯 Automation Loop

The complete automation loop:

1. **Detect Changes** - Monitor Vision repo for updates
2. **Analyze Impact** - Determine what needs documentation
3. **Generate Content** - Writer-Reviewer collaboration
4. **Save Output** - Store in outputs/ directory
5. **Update Memory** - Log enhancement in memory system
6. **Notify User** - Alert when content is ready

## 📚 Additional Resources

- [Agent Framework SDK Docs](https://learn.microsoft.com/en-us/azure/ai-services/agents/)
- [Microsoft Foundry](https://learn.microsoft.com/en-us/azure/ai-studio/)
- Vision project: `c:\project\vision\`

## 📝 License

Part of the Vision project. See main LICENSE file.
