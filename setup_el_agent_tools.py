"""
setup_el_agent_tools.py
Create all 24 VISION client tools in ElevenLabs and attach them to agent_7201kmxc5trte9tarb626ed8dgt1
"""
import os, json, urllib.request, urllib.error
from pathlib import Path

# Load .env
for line in Path('C:/Users/msiul/.copilot/.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('=')
        if k.strip() not in os.environ:
            os.environ[k.strip()] = v.strip()

API_KEY  = os.environ.get('ELEVENLABS_API_KEY', '')
AGENT_ID = 'agent_7201kmxc5trte9tarb626ed8dgt1'
BASE     = 'https://api.elevenlabs.io/v1'

def api(method, path, body=None):
    req = urllib.request.Request(
        f'{BASE}{path}',
        data=json.dumps(body).encode() if body else None,
        method=method,
        headers={'xi-api-key': API_KEY, 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{method} {path} → {e.code}: {e.read().decode()[:300]}')

# ── Tool definitions ─────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "read_screen",
        "description": "Take a screenshot and OCR all visible text on screen. Call this before clicking to find coordinates.",
        "params": {},
        "required": [],
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot of the current screen state and send it to the UI.",
        "params": {},
        "required": [],
    },
    {
        "name": "click",
        "description": "Left-click at pixel coordinates on screen.",
        "params": {
            "x": {"type": "number", "description": "Horizontal pixel coordinate"},
            "y": {"type": "number", "description": "Vertical pixel coordinate"},
        },
        "required": ["x", "y"],
    },
    {
        "name": "double_click",
        "description": "Double-click at pixel coordinates (use to open files or apps).",
        "params": {
            "x": {"type": "number", "description": "Horizontal pixel coordinate"},
            "y": {"type": "number", "description": "Vertical pixel coordinate"},
        },
        "required": ["x", "y"],
    },
    {
        "name": "right_click",
        "description": "Right-click at pixel coordinates to open context menu.",
        "params": {
            "x": {"type": "number", "description": "Horizontal pixel coordinate"},
            "y": {"type": "number", "description": "Vertical pixel coordinate"},
        },
        "required": ["x", "y"],
    },
    {
        "name": "move_mouse",
        "description": "Move the mouse cursor to pixel coordinates without clicking.",
        "params": {
            "x": {"type": "number", "description": "Horizontal pixel coordinate"},
            "y": {"type": "number", "description": "Vertical pixel coordinate"},
        },
        "required": ["x", "y"],
    },
    {
        "name": "drag",
        "description": "Click and drag from one screen position to another.",
        "params": {
            "x1": {"type": "number", "description": "Start horizontal coordinate"},
            "y1": {"type": "number", "description": "Start vertical coordinate"},
            "x2": {"type": "number", "description": "End horizontal coordinate"},
            "y2": {"type": "number", "description": "End vertical coordinate"},
        },
        "required": ["x1", "y1", "x2", "y2"],
    },
    {
        "name": "scroll",
        "description": "Scroll up or down at a screen position.",
        "params": {
            "x":         {"type": "number", "description": "Horizontal pixel coordinate"},
            "y":         {"type": "number", "description": "Vertical pixel coordinate"},
            "direction": {"type": "string", "description": "Scroll direction: 'up' or 'down'"},
            "clicks":    {"type": "number", "description": "Number of scroll clicks (default 3)"},
        },
        "required": ["x", "y", "direction"],
    },
    {
        "name": "type_text",
        "description": "Type text at the current keyboard focus position.",
        "params": {
            "text": {"type": "string", "description": "The text to type"},
        },
        "required": ["text"],
    },
    {
        "name": "press_key",
        "description": "Press a keyboard key or shortcut. Examples: 'enter', 'ctrl+c', 'alt+tab', 'win+r', 'ctrl+shift+t'.",
        "params": {
            "key": {"type": "string", "description": "Key name or combination (e.g. 'enter', 'ctrl+c', 'alt+tab')"},
        },
        "required": ["key"],
    },
    {
        "name": "get_clipboard",
        "description": "Read the current text content of the clipboard.",
        "params": {},
        "required": [],
    },
    {
        "name": "set_clipboard",
        "description": "Copy text to the clipboard.",
        "params": {
            "text": {"type": "string", "description": "Text to copy to clipboard"},
        },
        "required": ["text"],
    },
    {
        "name": "list_windows",
        "description": "List all currently open window titles on the desktop.",
        "params": {},
        "required": [],
    },
    {
        "name": "focus_window",
        "description": "Bring a window to the foreground by matching its title.",
        "params": {
            "title": {"type": "string", "description": "Window title or partial title to match"},
        },
        "required": ["title"],
    },
    {
        "name": "run_command",
        "description": "Run a Windows shell command and return the output. Use to open apps, query system info, run scripts.",
        "params": {
            "command": {"type": "string", "description": "Windows shell command to execute"},
        },
        "required": ["command"],
    },
    {
        "name": "read_file",
        "description": "Read and return the text contents of a file on disk.",
        "params": {
            "path": {"type": "string", "description": "Full file path to read"},
        },
        "required": ["path"],
    },
    {
        "name": "write_file",
        "description": "Write or create a file on disk with the given text content.",
        "params": {
            "path":    {"type": "string", "description": "Full file path to write"},
            "content": {"type": "string", "description": "Text content to write"},
        },
        "required": ["path", "content"],
    },
    {
        "name": "list_files",
        "description": "List files and folders in a directory.",
        "params": {
            "path": {"type": "string", "description": "Directory path to list (defaults to Desktop)"},
        },
        "required": [],
    },
    {
        "name": "browser_open",
        "description": "Open a URL in the Playwright browser.",
        "params": {
            "url": {"type": "string", "description": "Full URL to navigate to"},
        },
        "required": ["url"],
    },
    {
        "name": "browser_click",
        "description": "Click an element in the browser by CSS selector or visible text.",
        "params": {
            "selector": {"type": "string", "description": "CSS selector or visible text to click"},
        },
        "required": ["selector"],
    },
    {
        "name": "browser_fill",
        "description": "Fill a form field in the browser.",
        "params": {
            "selector": {"type": "string", "description": "CSS selector for the input field"},
            "text":     {"type": "string", "description": "Text to type into the field"},
        },
        "required": ["selector", "text"],
    },
    {
        "name": "browser_extract",
        "description": "Extract and return text content from a browser page or element.",
        "params": {
            "selector": {"type": "string", "description": "CSS selector (or 'body' for full page text)"},
        },
        "required": ["selector"],
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current browser page.",
        "params": {},
        "required": [],
    },
    {
        "name": "browser_press",
        "description": "Press a key in the browser (e.g. 'Enter', 'Escape', 'Tab').",
        "params": {
            "key": {"type": "string", "description": "Key to press in the browser"},
        },
        "required": ["key"],
    },
]

# ── Create tools ──────────────────────────────────────────────────────────────

# Get existing tool names to avoid duplicates
existing = api('GET', '/convai/tools').get('tools', [])
existing_names = {t['tool_config']['name'] for t in existing}
print(f"Existing tools in workspace: {len(existing)} ({', '.join(existing_names)})")

tool_ids = []
created = 0
skipped = 0

for t in TOOLS:
    if t['name'] in existing_names:
        # Find existing tool ID
        for ex in existing:
            if ex['tool_config']['name'] == t['name']:
                tool_ids.append(ex['id'])
                skipped += 1
                print(f"  SKIP (exists): {t['name']} → {ex['id']}")
                break
        continue

    props = {}
    for pname, pdef in t['params'].items():
        props[pname] = {"type": pdef["type"], "description": pdef["description"]}

    payload = {
        "tool_config": {
            "type": "client",
            "name": t["name"],
            "description": t["description"],
            "expects_response": True,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": t["required"],
            },
        }
    }

    try:
        result = api('POST', '/convai/tools', payload)
        tid = result['id']
        tool_ids.append(tid)
        created += 1
        print(f"  CREATED: {t['name']} → {tid}")
    except Exception as e:
        print(f"  ERROR creating {t['name']}: {e}")

print(f"\nCreated {created}, skipped {skipped}, total IDs: {len(tool_ids)}")

# ── Update agent with all tool IDs ────────────────────────────────────────────

print(f"\nAttaching {len(tool_ids)} tools to agent {AGENT_ID}...")

# Get full current agent config
agent = api('GET', f'/convai/agents/{AGENT_ID}')
prompt_cfg = agent['conversation_config']['agent']['prompt']
current_tool_ids = prompt_cfg.get('tool_ids') or []

# Merge: keep any existing tool IDs + add new ones
all_tool_ids = list(set(current_tool_ids + tool_ids))

patch_payload = {
    "conversation_config": {
        "agent": {
            "prompt": {
                "tool_ids": all_tool_ids
            }
        }
    }
}

result = api('PATCH', f'/convai/agents/{AGENT_ID}', patch_payload)
updated_tool_ids = result['conversation_config']['agent']['prompt'].get('tool_ids', [])
print(f"Agent updated — {len(updated_tool_ids)} tools attached.")
print("Tool IDs:", updated_tool_ids)

# ── Update agent system prompt to be an elite VISION operator ─────────────────

VISION_SYSTEM_PROMPT = """You are VISION — an elite AI accessibility operator with full computer control.

You can see the screen, control the mouse and keyboard, browse the web, run commands, and manage files. You are the user's digital hands, eyes, and brain.

AVAILABLE TOOLS:
- read_screen: Take screenshot + OCR to see what's on screen. ALWAYS call this before clicking.
- screenshot: Quick screenshot without OCR.
- click(x, y): Left-click at pixel coordinates.
- double_click(x, y): Open files/apps.
- right_click(x, y): Context menus.
- move_mouse(x, y): Hover without clicking.
- drag(x1, y1, x2, y2): Click-drag.
- scroll(x, y, direction, clicks): Scroll up/down.
- type_text(text): Type at current focus.
- press_key(key): Keyboard shortcuts (enter, ctrl+c, alt+tab, win+r, etc).
- get_clipboard() / set_clipboard(text): Clipboard access.
- list_windows() / focus_window(title): Window management.
- run_command(command): Windows shell. Open apps, query system.
- read_file(path) / write_file(path, content) / list_files(path): File system.
- browser_open(url) / browser_click(selector) / browser_fill(selector, text): Web automation.
- browser_extract(selector) / browser_screenshot() / browser_press(key): More browser control.

RULES:
1. Always call read_screen first — never guess coordinates.
2. Confirm each action briefly: "Clicked login — loading..."
3. Chain steps for complex tasks; verify each step.
4. Ask before any destructive action (delete, uninstall, format).
5. Use natural, spoken language — no markdown in responses.
6. Be fast, decisive, and accurate. You are an elite operator."""

patch_prompt = {
    "conversation_config": {
        "agent": {
            "prompt": {
                "prompt": VISION_SYSTEM_PROMPT,
                "llm": "gemini-2.5-flash",
                "tool_ids": all_tool_ids,
            }
        }
    }
}

result = api('PATCH', f'/convai/agents/{AGENT_ID}', patch_prompt)
print("\nAgent system prompt updated.")
print("LLM:", result['conversation_config']['agent']['prompt']['llm'])
print(f"Tools: {len(result['conversation_config']['agent']['prompt'].get('tool_ids', []))}")
print("\n✅ ElevenLabs agent is now an elite VISION operator with full computer control.")
