# Vision Content Collaboration Workflow

A multi-agent Writer-Reviewer system using Microsoft Agent Framework SDK for automated content creation and refinement.

## Overview

This workflow implements a collaborative content creation process where:

1. **Writer Agent** creates initial content based on user requirements
2. **Reviewer Agent** provides actionable feedback for improvement
3. **Collaboration Loop** iterates until content meets quality standards
4. **Final Output** is refined content ready for use

## Features

- ✅ **Multi-Agent Collaboration** - Writer and Reviewer agents working together
- ✅ **Iterative Refinement** - Up to 3 rounds of review and revision
- ✅ **Multiple Content Types** - Documentation, code, blog posts, reviews
- ✅ **Quality Assurance** - Structured review criteria (clarity, accuracy, completeness)
- ✅ **HTTP Server** - Deployable as a web service
- ✅ **VS Code Integration** - Debug configurations for Agent Inspector

## Architecture

```
User Request
    ↓
┌─────────────────┐
│  Writer Agent   │ → Creates initial content
└────────┬────────┘
         ↓
┌─────────────────┐
│ Reviewer Agent  │ → Provides feedback
└────────┬────────┘
         ↓
    [Approved?]
    ↓ YES    ↓ NO
Final    ←─── Revision
Output       Loop
```

## Quick Start

### 1. Install Dependencies

```powershell
# Navigate to workflow directory
cd c:\project\vision\agent_workflow

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install requirements (IMPORTANT: Install in this order!)
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy template
copy .env.template .env

# Edit .env with your Foundry credentials
notepad .env
```

### 3. Run the Workflow

```powershell
# Run example collaboration
python workflow.py

# Or run as HTTP server
python workflow.py server
```

## Usage

### Direct Execution

```python
import asyncio
from workflow import run_collaboration

async def main():
    content = await run_collaboration(
        topic="Getting Started with Vision",
        content_type="documentation",
        requirements=[
            "Clear installation steps",
            "Basic usage examples",
            "Troubleshooting section"
        ]
    )
    print(content)

asyncio.run(main())
```

### HTTP API

When running as a server:

```bash
# Start server
python workflow.py server

# Send request
curl -X POST http://localhost:8000/create_content \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "text": "Create documentation about Vision Memory System"}
    ]
  }'
```

## Content Types

| Type | Description | Use Case |
|------|-------------|----------|
| `documentation` | Technical docs, guides | README, API docs |
| `code` | Code examples, tutorials | Functions, classes |
| `blog` | Articles, posts | Announcements, tutorials |
| `review` | Analysis, comparisons | Tool comparisons |

## Review Criteria

The Reviewer Agent evaluates content on:

1. **Clarity** - Easy to understand, logical structure
2. **Accuracy** - Technical correctness, valid examples
3. **Completeness** - All necessary aspects covered
4. **Engagement** - Interesting, maintains attention
5. **Style** - Appropriate tone, consistent formatting
6. **Conventions** - Follows project standards

## Integration with Vision

This workflow can enhance the Vision project by:

1. **Auto-generating Documentation** - Create docs from code
2. **Code Review Assistance** - Review PR descriptions
3. **Blog Post Creation** - Generate content from features
4. **Tutorial Generation** - Create guides from workflows

### Example: Generate Vision Documentation

```python
from content_collaboration import ContentCollaborationWorkflow, WorkflowConfig, ContentRequest

async def generate_vision_docs():
    config = WorkflowConfig()
    workflow = ContentCollaborationWorkflow(config)

    request = ContentRequest(
        topic="OpenClaw Elite Phone Control",
        content_type="documentation",
        requirements=[
            "Explain ADB integration",
            "Show interactive menu options",
            "Include troubleshooting",
            "Code examples"
        ],
        context="Vision project phone control feature"
    )

    result = await workflow.execute(request)
    # Result saved to outputs/ directory
```

## Project Structure

```
agent_workflow/
├── content_collaboration.py  # Core workflow implementation
├── workflow.py               # Entry points and HTTP server
├── requirements.txt          # Dependencies
├── .env.template            # Environment template
├── README.md                # This file
├── outputs/                 # Generated content
└── .vscode/
    └── launch.json          # Debug configurations
```

## Debugging

### With VS Code

1. Open `agent_workflow` folder in VS Code
2. Set breakpoints in `content_collaboration.py`
3. Press F5 and select "Agent Dev CLI: Content Workflow"

### With AI Toolkit Agent Inspector

1. Start workflow with debugpy:
   ```powershell
   python -m debugpy --listen 5678 --wait-for-client workflow.py
   ```
2. In VS Code, run "AI Toolkit Agent Inspector" configuration
3. Open Agent Inspector in browser

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FOUNDRY_PROJECT_ENDPOINT` | Azure Foundry endpoint | Yes |
| `FOUNDRY_MODEL_DEPLOYMENT_NAME` | Model deployment name | Yes |
| `WORKFLOW_MAX_ITERATIONS` | Max review cycles | No (default: 3) |
| `WORKFLOW_OUTPUT_DIR` | Output directory | No (default: ./outputs) |

## Troubleshooting

### Import Errors

Ensure you're using the virtual environment:
```powershell
.\venv\Scripts\Activate
```

### Authentication Issues

Login to Azure:
```powershell
az login
```

### Model Not Found

Verify your `.env` file has correct Foundry credentials.

## License

Part of the Vision project. See main LICENSE file.
