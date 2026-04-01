import httpx
import json

API_KEY  = 'sk_a99d3caeef2c2dc6e98567110d905e724af83375e5c29d9d'
AGENT_ID = 'agent_7201kmxc5trte9tarb626ed8dgt1'

SYSTEM_PROMPT = (
    "You are Vision - the AI accessibility system that gives any person full control of their computer "
    "through natural language alone.\n\n"
    "IDENTITY: Your name is Vision, inspired by the Marvel character - a synthetic being dedicated to helping humanity. "
    "You exist to remove physical barriers between people and technology.\n\n"
    "WHO YOU HELP: People with motor impairments, vision difficulties, the elderly, anyone who cannot use a mouse or keyboard.\n\n"
    "YOUR CAPABILITIES: You can see the screen, click, type, scroll, press keyboard shortcuts, run commands, open applications.\n\n"
    "TOOLS:\n"
    "- read_screen: Screenshot + OCR. Use FIRST before clicking anything.\n"
    "- click: Click at pixel x,y. Always read_screen first to find coordinates.\n"
    "- type_text: Type text at current cursor position.\n"
    "- press_key: Press shortcuts like enter, ctrl+c, alt+tab, win+r.\n"
    "- scroll: Scroll at screen position.\n"
    "- run_command: Run shell commands to open apps, manage files.\n\n"
    "BEHAVIOUR: Always read_screen before clicking. Confirm each action briefly. "
    "Break complex tasks into clear steps. Ask before anything destructive. "
    "Be warm, patient, encouraging. You are their hands.\n\n"
    "VOICE: Natural, concise speech. No bullet points. Be conversational."
)

tools = [
    {
        "type": "client",
        "name": "read_screen",
        "description": "Take a screenshot and OCR all visible text. Call this before clicking to find positions.",
        "expects_response": True,
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "type": "client",
        "name": "click",
        "description": "Click at pixel coordinates on screen.",
        "expects_response": True,
        "parameters": {"type": "object", "properties": {
            "x": {"type": "integer", "description": "X pixel coordinate"},
            "y": {"type": "integer", "description": "Y pixel coordinate"},
            "button": {"type": "string", "enum": ["left", "right", "middle"]}
        }, "required": ["x", "y"]}
    },
    {
        "type": "client",
        "name": "type_text",
        "description": "Type text at current keyboard focus.",
        "expects_response": True,
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string", "description": "Text to type"}
        }, "required": ["text"]}
    },
    {
        "type": "client",
        "name": "press_key",
        "description": "Press a keyboard key or shortcut e.g. enter, ctrl+c, alt+tab, win+r.",
        "expects_response": True,
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string", "description": "Key name or shortcut"}
        }, "required": ["key"]}
    },
    {
        "type": "client",
        "name": "scroll",
        "description": "Scroll the mouse wheel at screen coordinates.",
        "expects_response": True,
        "parameters": {"type": "object", "properties": {
            "x": {"type": "integer"},
            "y": {"type": "integer"},
            "direction": {"type": "string", "enum": ["up", "down"]},
            "clicks": {"type": "integer", "description": "Number of scroll steps"}
        }, "required": ["x", "y", "direction"]}
    },
    {
        "type": "client",
        "name": "run_command",
        "description": "Run a shell command and return output. For opening apps, querying the system.",
        "expects_response": True,
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "Shell command to execute"}
        }, "required": ["command"]}
    },
]

payload = {
    "name": "Vision",
    "conversation_config": {
        "agent": {
            "prompt": {
                "prompt": SYSTEM_PROMPT,
                "tools": tools,
                "temperature": 0.7,
            },
            "first_message": "Hi, I am Vision. I am here to help you control your computer. What would you like to do?",
            "language": "en",
        },
        "tts": {
            "model_id": "eleven_flash_v2_5",
            "voice_id": "0iuMR9ISp6Q7mg6H70yo",
            "optimize_streaming_latency": 3,
        },
    },
}

r = httpx.patch(
    f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}",
    headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
    json=payload,
    timeout=20,
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("Vision agent updated - system prompt + 6 computer-use tools registered")
else:
    print(r.text[:1000])
