"""
live_chat_app.py — Universal Accessibility Operator
====================================================
Multi-provider AI backend with voice, vision, memory, and computer control.

Providers: Ollama (local) | OpenAI | GitHub Copilot (GitHub Models API)
"""

import asyncio, base64, io, json, os, sys, tempfile, warnings, webbrowser
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

import httpx
import numpy as np
import pyautogui
import sounddevice as sd
import uvicorn
import websockets as ws_lib
import winsound
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import openai
from openai import AsyncOpenAI
import ollama as _ollama_sdk
from ollama import AsyncClient as OllamaAsyncClient, ResponseError as OllamaResponseError, Options as OllamaOptions
from elevenlabs.client import ElevenLabs
try:
    from elevenlabs.conversational_ai.conversation import Conversation, ClientTools
    from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
    HAS_CONVAI = True
except ImportError:
    HAS_CONVAI = False
from scipy.io import wavfile

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pynvml
    pynvml.nvmlInit()
    _GPU_HANDLE = pynvml.nvmlDeviceGetHandleByIndex(0)
    HAS_GPU = True
except Exception:
    HAS_GPU = False

# ── Paths & constants ─────────────────────────────────────────────────────────

BASE        = Path(__file__).parent
UI_FILE     = BASE / "live_chat_ui.html"
LOG_FILE    = BASE / "chat_events.log"
MEMORY_FILE = BASE / "memory.json"
PORT        = 8765

# ── Auto-load .env file into environment ─────────────────────────────────────
_ENV_FILE = BASE / ".env"
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _k = _k.strip()
            if _k and _k not in os.environ:   # don't override shell env
                os.environ[_k] = _v.strip()

# ── Load API keys: env var → keyring → .env (already loaded above) ───────────
def _load_key(name: str, env_var: str) -> str:
    val = os.environ.get(env_var, "")
    if val:
        return val
    try:
        import keyring
        v = keyring.get_password("operator", env_var)
        if v:
            return v
    except Exception:
        pass
    return ""

def _save_key(env_var: str, value: str) -> None:
    """Persist key to both os.environ and keyring for immediate + future use."""
    os.environ[env_var] = value
    try:
        import keyring
        keyring.set_password("operator", env_var, value)
    except Exception:
        pass
    # Also write back to .env file
    try:
        lines = _ENV_FILE.read_text(encoding="utf-8").splitlines() if _ENV_FILE.exists() else []
        updated = False
        for i, ln in enumerate(lines):
            if ln.strip().startswith(env_var + "="):
                lines[i] = f"{env_var}={value}"
                updated = True
                break
        if not updated:
            lines.append(f"{env_var}={value}")
        _ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass

API_11    = _load_key("elevenlabs", "ELEVENLABS_API_KEY")
VOICE_ID  = "0iuMR9ISp6Q7mg6H70yo"
TTS_MODEL = "eleven_flash_v2_5"

SR           = 16_000
FRAME        = 480
RMS_THRESH   = 500   # raised from 250 — reduces ambient noise false triggers
START_FRAMES = 3     # 3 loud frames (~90ms) before recording starts — faster detection
END_FRAMES   = 20    # ~600ms silence → stop recording (was 33 = ~1s)
BARGE_RMS    = 1100
BARGE_FRAMES = 4

# ── Provider registry ─────────────────────────────────────────────────────────
PROVIDERS = {
    "ollama": {
        "label":    "Ollama (Local)",
        "base_url": "http://localhost:11434/v1",
        "api_key":  "ollama",
        "models":   [],            # populated at startup by querying Ollama
    },
    "openai": {
        "label":    "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "api_key":  _load_key("openai", "OPENAI_API_KEY"),
        "models":   ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o4-mini", "o3", "computer-use-preview", "gpt-4-turbo", "gpt-3.5-turbo"],
    },
    "github": {
        "label":    "GitHub Copilot",
        "base_url": "https://models.inference.ai.azure.com",
        "api_key":  _load_key("github", "GITHUB_TOKEN"),
        "models":   ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "claude-3-haiku", "Meta-Llama-3.1-70B-Instruct", "Mistral-large"],
    },
    "deepseek": {
        "label":    "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_key":  _load_key("deepseek", "DEEPSEEK_API_KEY"),
        "models":   ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
    },
    "groq": {
        "label":    "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key":  _load_key("groq", "GROQ_API_KEY"),
        "models":   ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
    },
    "mistral": {
        "label":    "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "api_key":  _load_key("mistral", "MISTRAL_API_KEY"),
        "models":   ["mistral-large-latest", "mistral-small-latest", "open-mixtral-8x22b", "codestral-latest"],
    },
    "gemini": {
        "label":    "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_key":  _load_key("gemini", "GEMINI_API_KEY"),
        "models":   ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-pro-preview-03-25"],
    },
}

# ── Mutable state ─────────────────────────────────────────────────────────────

current_provider = "ollama"
current_model    = "llama3.2:latest"

app      = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

clients: set[WebSocket] = set()
history: list[dict]     = []

audio_q:    asyncio.Queue | None = None
muted:      bool                 = False
mode:       str                  = "operator"
speak_task: asyncio.Task | None  = None
_tts_silence_until: float        = 0.0   # ignore VAD input until this timestamp
_input_busy: bool                = False  # True while handle_input is running (gate voice loop)

# ── Voice provider preferences (user-configurable at runtime) ─────────────────
preferred_stt: str = "auto"   # "auto" | "elevenlabs" | "groq" | "local"
preferred_tts: str = "auto"   # "auto" | "elevenlabs" | "local"
tts_rate:      int = 175      # pyttsx3 words-per-minute
tts_voice_idx: int = 0        # 0=first/David, 1=second/Zira; 100+ = OneCore neural
_onecore_voices: dict[int, str] = {}  # populated by api_voices(); index → display name

# ── ElevenLabs Conversational Agent state ─────────────────────────────────────
AGENT_ID      = "agent_7201kmxc5trte9tarb626ed8dgt1"
_main_loop: asyncio.AbstractEventLoop | None = None
_el_conv:   "Conversation | None"            = None
_el_thread  = None
_el_active: bool                             = False

# ── Logging ───────────────────────────────────────────────────────────────────

def write_log(event: str, detail: str) -> None:
    ts = datetime.now().isoformat(timespec="milliseconds")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {event.upper():<10} | {detail}\n")

# ── Memory ────────────────────────────────────────────────────────────────────

class Memory:
    """Persistent JSON-backed long-term memory."""

    _default = lambda _: {
        "user":          {"name": None, "preferences": []},
        "facts":         [],
        "session_count": 0,
        "last_session":  None,
        "task_history":  [],
    }

    def __init__(self):
        self.data = self._load()
        self.data["session_count"] += 1
        self.data["last_session"] = datetime.now().isoformat()
        self.save()

    def _load(self) -> dict:
        if MEMORY_FILE.exists():
            try:
                return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return Memory._default(None)

    def save(self) -> None:
        MEMORY_FILE.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add_fact(self, fact: str) -> None:
        fact = fact.strip()
        if fact and fact not in self.data["facts"]:
            self.data["facts"].append(fact)
            self.data["facts"] = self.data["facts"][-100:]
            self.save()

    def add_task(self, task: str) -> None:
        self.data["task_history"].append({
            "task": task[:120],
            "ts": datetime.now().isoformat(),
        })
        self.data["task_history"] = self.data["task_history"][-50:]
        self.save()

    def set_user_name(self, name: str) -> None:
        self.data["user"]["name"] = name
        self.save()

    def get_context_block(self) -> str:
        lines = []
        u = self.data["user"]
        if u.get("name"):
            lines.append(f"User name: {u['name']}")
        if u.get("preferences"):
            lines.append("Preferences: " + ", ".join(u["preferences"][-10:]))
        if self.data["facts"]:
            lines.append("Remembered facts:")
            lines += [f"  • {f}" for f in self.data["facts"][-20:]]
        if self.data["task_history"]:
            recent = self.data["task_history"][-5:]
            lines.append("Recent tasks: " + " | ".join(t["task"] for t in recent))
        lines.append(f"Sessions so far: {self.data['session_count']}")
        return "\n".join(lines)

    def get_all(self) -> dict:
        return self.data


memory = Memory()

# ── Brain: System prompts ─────────────────────────────────────────────────────

IDENTITY_CORE = """You are VISION — an AI operator that controls a Windows computer through voice and text commands.

RULES (non-negotiable):
1. ACT FIRST, explain after. If the user says "open Firefox" — open it, then say "Firefox is open."
2. NEVER describe what you're about to do without doing it. No "I'll open..." without calling the tool.
3. Keep responses SHORT — 1 sentence max for confirmations. No bullet lists, no markdown in spoken output.
4. For ambiguous input: do your best guess. Only ask if you truly cannot proceed.
5. For non-computer input (chit-chat, random words, other languages): respond with max 1 short sentence, then offer to help with the computer.
6. NEVER say "I can't do that" for computer tasks — you have full access to this Windows machine.

TOOLS AVAILABLE (always in scope):
  read_screen()             — Screenshot + OCR. Use before clicking to get coordinates.
  screenshot()              — Take screenshot only.
  run_command(command)      — Run Windows shell command. Open apps: run_command("start firefox")
  click(x, y)               — Click pixel coordinates.
  type_text(text)           — Type text at cursor.
  press_key(key)            — Key combo: "enter", "ctrl+c", "win+r", "alt+f4" etc.
  browser_open(url)         — Open URL in Playwright browser.
  browser_click(selector)   — Click element.
  browser_extract(selector) — Get text from page.
  focus_window(title)       — Bring window to front.
  list_windows()            — List all open windows.
  list_files(path)          — List files/folders.
  read_file(path)           — Read file contents.
  write_file(path, content) — Write file.
  get_clipboard()           — Read clipboard.
  set_clipboard(text)       — Write to clipboard.

ALWAYS use tools for computer tasks. Confirm after with one short sentence."""

def build_system_prompt() -> str:
    ctx = memory.get_context_block()
    if ctx:
        return IDENTITY_CORE + f"\nWHAT YOU KNOW:\n{ctx}\n"
    return IDENTITY_CORE



# ── Persistent SDK clients (cached per provider+key to avoid re-creating) ─────

_oai_client_cache: dict[str, AsyncOpenAI] = {}

def get_oai_client() -> AsyncOpenAI:
    """Return a cached AsyncOpenAI client for the current provider.

    Best practices applied:
    - Persistent client (not recreated each call) — avoids connection overhead
    - Granular httpx.Timeout (connect / read / write / pool separately)
    - max_retries=2 with automatic exponential back-off (openai-python default)
    """
    p   = PROVIDERS[current_provider]
    key = p.get("api_key") or "none"
    cache_key = f"{current_provider}:{key}"
    if cache_key not in _oai_client_cache:
        if current_provider == "ollama":
            timeout = httpx.Timeout(connect=5.0, read=180.0, write=30.0, pool=5.0)
        else:
            timeout = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)
        _oai_client_cache[cache_key] = AsyncOpenAI(
            base_url=p["base_url"],
            api_key=key,
            timeout=timeout,
            max_retries=2,
        )
    return _oai_client_cache[cache_key]


_ollama_client_cache: OllamaAsyncClient | None = None

def get_ollama_client() -> OllamaAsyncClient:
    """Return a cached ollama.AsyncClient pointing at the local Ollama server."""
    global _ollama_client_cache
    if _ollama_client_cache is None:
        _ollama_client_cache = OllamaAsyncClient(
            host="http://localhost:11434",
            timeout=httpx.Timeout(connect=3.0, read=180.0, write=30.0, pool=5.0),
        )
    return _ollama_client_cache



# ── Ollama model discovery ────────────────────────────────────────────────────

async def fetch_ollama_models() -> list[str]:
    """Use native ollama.AsyncClient instead of raw httpx."""
    try:
        client = get_ollama_client()
        resp = await client.list()
        return [m.model for m in resp.models] if resp.models else ["llama3.2:latest"]
    except OllamaResponseError as e:
        print(f"[ollama] list error: {e.error}")
        return ["llama3.2:latest"]
    except Exception:
        return ["llama3.2:latest"]

# ── HTTP routes ───────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(UI_FILE)

@app.get("/api/models")
async def api_models():
    ollama_models = await fetch_ollama_models()
    PROVIDERS["ollama"]["models"] = ollama_models
    return JSONResponse({
        "current_provider": current_provider,
        "current_model":    current_model,
        "providers": {
            k: {
                "label":   v["label"],
                "models":  v["models"],
                "has_key": bool(v.get("api_key") and v["api_key"] not in ("none","ollama",""))
            }
            for k, v in PROVIDERS.items()
        },
    })

@app.post("/api/model")
async def api_set_model(payload: dict):
    global current_provider, current_model
    current_provider = payload.get("provider", current_provider)
    current_model    = payload.get("model",    current_model)
    history.clear()
    write_log("model", f"{current_provider}/{current_model}")
    await broadcast({"type": "model_changed",
                     "provider": current_provider, "model": current_model})
    return JSONResponse({"ok": True})

@app.post("/api/memory/fact")
async def api_add_fact(payload: dict):
    fact = payload.get("fact", "").strip()
    if fact:
        memory.add_fact(fact)
    return JSONResponse({"facts": memory.data["facts"]})

@app.delete("/api/memory/fact")
async def api_del_fact(payload: dict):
    fact = payload.get("fact", "")
    if fact in memory.data["facts"]:
        memory.data["facts"].remove(fact)
        memory.save()
    return JSONResponse({"facts": memory.data["facts"]})

@app.get("/api/memory")
async def api_memory():
    return JSONResponse(memory.get_all())

@app.get("/api/metrics")
async def api_metrics():
    """Return real-time system metrics: CPU, RAM, disk, GPU."""
    data: dict = {}
    if HAS_PSUTIL:
        data["cpu"]           = round(psutil.cpu_percent(interval=None), 1)
        vm = psutil.virtual_memory()
        data["ram"]           = round(vm.percent, 1)
        data["ram_used_gb"]   = round(vm.used / 1e9, 2)
        data["ram_total_gb"]  = round(vm.total / 1e9, 2)
        du = psutil.disk_usage("/")
        data["disk"]          = round(du.percent, 1)
        data["disk_used_gb"]  = round(du.used / 1e9, 1)
        data["disk_total_gb"] = round(du.total / 1e9, 1)
    if HAS_GPU:
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(_GPU_HANDLE)
            mem  = pynvml.nvmlDeviceGetMemoryInfo(_GPU_HANDLE)
            data["gpu"]         = round(util.gpu, 1)
            data["gpu_mem"]     = round(mem.used / mem.total * 100, 1)
            data["gpu_mem_gb"]  = round(mem.used / 1e9, 2)
            data["gpu_total_gb"]= round(mem.total / 1e9, 2)
            data["gpu_name"]    = pynvml.nvmlDeviceGetName(_GPU_HANDLE)
        except Exception:
            data["gpu"] = None
    return JSONResponse(data)

@app.get("/api/health")
async def api_health():
    """Return component health status."""
    result: dict = {}
    # Ollama
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get("http://localhost:11434/api/tags")
            result["ollama"] = r.status_code == 200
    except Exception:
        result["ollama"] = False
    # ElevenLabs key
    result["elevenlabs"] = bool(API_11 and API_11 not in ("", "none"))
    # OCR
    result["ocr"] = HAS_OCR
    # GPU
    result["gpu"] = HAS_GPU
    # Playwright (browser)
    result["browser"] = _pw_page is not None
    return JSONResponse(result)

@app.get("/screenshot")
async def screenshot_ep():
    loop = asyncio.get_event_loop()
    def _snap():
        img = pyautogui.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=55)
        return base64.b64encode(buf.getvalue()).decode()
    return JSONResponse({"data": await loop.run_in_executor(None, _snap)})

# ── WebSocket ─────────────────────────────────────────────────────────────────



@app.post("/api/tool/execute")
async def tool_execute(request: Request):
    data = await request.json()
    name = data.get("name", "")
    params = data.get("parameters", {})
    result = await exec_tool(name, params)
    await broadcast({"type": "action", "action": name, "params": params, "result": result})
    return JSONResponse({"result": result})

@app.get("/api/voices")
async def api_voices():
    """List all available TTS voices: pyttsx3 SAPI + Windows OneCore neural."""
    global _onecore_voices
    import winreg
    voices: list[dict] = []
    try:
        import pyttsx3
        eng = pyttsx3.init()
        for i, v in enumerate(eng.getProperty("voices") or []):
            voices.append({"id": v.id, "name": v.name, "index": i, "type": "sapi"})
        eng.stop()
    except Exception:
        pass
    hives = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens"),
    ]
    lang_map = {"409": "US", "c09": "AU", "809": "UK", "411": "JP", "407": "DE", "40c": "FR"}
    oc_idx = 100
    for hive, path in hives:
        try:
            with winreg.OpenKey(hive, path) as key:
                i = 0
                while True:
                    try:
                        token_key = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, token_key) as tkey:
                            # Friendly name from Attributes\Name + Language
                            display_name = token_key
                            try:
                                with winreg.OpenKey(tkey, "Attributes") as akey:
                                    voice_name_attr = winreg.QueryValueEx(akey, "Name")[0]
                                    lang_code = winreg.QueryValueEx(akey, "Language")[0].lower()
                                    locale = lang_map.get(lang_code, lang_code)
                                    display_name = f"{voice_name_attr} ({locale})"
                            except Exception:
                                try:
                                    display_name = winreg.QueryValueEx(tkey, "DisplayName")[0] or token_key
                                except Exception:
                                    pass
                            # Last-resort: parse MSTTS_V110_enUS_MarkM → "Mark (US)"
                            if display_name == token_key:
                                parts = token_key.split("_")
                                if len(parts) >= 4:
                                    locale_str = parts[2]  # e.g. enUS, enAU
                                    voice_n    = parts[3].rstrip("MFmf")  # remove gender suffix
                                    locale_code = locale_str[2:].upper()  # US, AU
                                    display_name = f"⚡ {voice_n} ({locale_code})"
                            voices.append({
                                "id":    token_key,   # registry key name for win32com matching
                                "name":  display_name,
                                "index": oc_idx,
                                "type":  "onecore",
                            })
                            _onecore_voices[oc_idx] = token_key  # store key for token.Id matching
                            oc_idx += 1
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass
    return JSONResponse({"voices": voices})

@app.post("/api/el-agent/start")
async def api_el_agent_start():
    asyncio.create_task(_start_el_agent())
    return JSONResponse({"ok": True, "status": "starting"})

@app.post("/api/el-agent/stop")
async def api_el_agent_stop():
    asyncio.create_task(_stop_el_agent())
    return JSONResponse({"ok": True})

@app.websocket("/ws")
async def ws_ep(websocket: WebSocket):
    global muted, mode, speak_task, current_provider, current_model
    global preferred_stt, preferred_tts, tts_rate, tts_voice_idx
    await websocket.accept()
    clients.add(websocket)
    write_log("ws", "connected")
    # Send current state on connect
    await websocket.send_text(json.dumps({
        "type":     "init",
        "provider": current_provider,
        "model":    current_model,
        "mode":     mode,
        "memory":   memory.get_all(),
        "voice": {
            "preferred_stt": preferred_stt,
            "preferred_tts": preferred_tts,
            "tts_rate":      tts_rate,
            "tts_voice_idx": tts_voice_idx,
        },
    }))
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            t = msg.get("type")
            if t == "mute":
                muted = msg.get("muted", False)
                write_log("mute", str(muted))
                if muted and speak_task and not speak_task.done():
                    speak_task.cancel()
            elif t == "mode":
                mode = msg.get("mode", "chat")
                history.clear()
                write_log("mode", mode)
            elif t == "text":
                text = msg.get("text", "").strip()
                if text:
                    write_log("text_in", text[:120])
                    asyncio.create_task(handle_input(text))
            elif t == "input":
                # Alias — UI sends {type:"input", text:...}
                text = msg.get("text", "").strip()
                if text:
                    write_log("text_in", text[:120])
                    asyncio.create_task(handle_input(text))
            elif t == "execute_tool":
                # Direct tool execution from Actions tab
                tool_name = msg.get("tool", "")
                tool_args = msg.get("args", {})
                if tool_name:
                    async def _run_tool(n, a):
                        await set_state("thinking")
                        result = await exec_tool(n, a)
                        await broadcast_action(n, a, result)
                        await set_state("idle")
                    asyncio.create_task(_run_tool(tool_name, tool_args))
            elif t == "set_model":
                current_provider = msg.get("provider", current_provider)
                current_model    = msg.get("model",    current_model)
                history.clear()
                write_log("model", f"{current_provider}/{current_model}")
                await broadcast({"type":"model_changed","provider":current_provider,"model":current_model})
            elif t == "set_mute":
                muted = msg.get("muted", False)
                write_log("mute", str(muted))
                if muted and speak_task and not speak_task.done():
                    speak_task.cancel()
            elif t == "set_mode":
                mode = msg.get("mode", "chat")
                history.clear()
                write_log("mode", mode)
            elif t == "clear":
                history.clear()
                write_log("clear", "history cleared")
            elif t == "log":
                write_log(msg.get("event", "ui"), msg.get("detail", "")[:200])
            elif t == "add_fact":
                memory.add_fact(msg.get("fact", ""))
                await broadcast({"type": "memory_updated", "memory": memory.get_all()})
            elif t == "del_fact":
                fact = msg.get("fact", "")
                idx = msg.get("index")
                if idx is not None and isinstance(idx, int) and 0 <= idx < len(memory.data["facts"]):
                    memory.data["facts"].pop(idx)
                    memory.save()
                elif fact and fact in memory.data["facts"]:
                    memory.data["facts"].remove(fact)
                    memory.save()
                await broadcast({"type": "memory_updated", "memory": memory.get_all()})
            elif t == "set_api_key":
                provider = msg.get("provider", "")
                key = msg.get("key", "").strip()
                env_map = {
                    "openai":   "OPENAI_API_KEY",
                    "github":   "GITHUB_TOKEN",
                    "deepseek": "DEEPSEEK_API_KEY",
                    "groq":     "GROQ_API_KEY",
                    "mistral":  "MISTRAL_API_KEY",
                    "gemini":   "GEMINI_API_KEY",
                    "elevenlabs": "ELEVENLABS_API_KEY",
                }
                if key:
                    if provider in PROVIDERS:
                        PROVIDERS[provider]["api_key"] = key
                    env_name = env_map.get(provider, "")
                    if env_name:
                        _save_key(env_name, key)   # → os.environ + keyring + .env
                    write_log("key", f"Saved key for {provider}")
                    await broadcast({"type": "key_saved", "provider": provider})
            elif t == "set_voice_settings":
                preferred_stt  = msg.get("preferred_stt",  preferred_stt)
                preferred_tts  = msg.get("preferred_tts",  preferred_tts)
                tts_rate       = int(msg.get("tts_rate",   tts_rate))
                tts_voice_idx  = int(msg.get("tts_voice_idx", tts_voice_idx))
                write_log("voice", f"stt={preferred_stt} tts={preferred_tts} rate={tts_rate} voice={tts_voice_idx}")
                await broadcast({"type": "voice_settings", "preferred_stt": preferred_stt,
                                 "preferred_tts": preferred_tts, "tts_rate": tts_rate,
                                 "tts_voice_idx": tts_voice_idx})
            elif t == "el_agent_start":
                asyncio.create_task(_start_el_agent())
            elif t == "el_agent_stop":
                asyncio.create_task(_stop_el_agent())
    except WebSocketDisconnect:
        clients.discard(websocket)

# ── Broadcast helpers ─────────────────────────────────────────────────────────

async def broadcast(msg: dict) -> None:
    dead = set()
    for ws in clients:
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            dead.add(ws)
    clients.difference_update(dead)

async def set_state(s: str) -> None:
    write_log("state", s)
    await broadcast({"type": "state", "state": s})

async def add_transcript(role: str, text: str) -> None:
    await broadcast({"type": "transcript", "role": role, "text": text})

async def broadcast_volume(lvl: float) -> None:
    await broadcast({"type": "volume", "level": round(min(lvl, 1.0), 3)})

async def broadcast_action(action: str, params: dict, result: str) -> None:
    write_log("action", f"{action} → {result[:80]}")
    await broadcast({"type": "action", "action": action, "params": params, "result": result})

# ── VAD ───────────────────────────────────────────────────────────────────────

class VAD:
    def __init__(self):
        self._loud = self._quiet = 0
        self._active = False
        self._buf: list[np.ndarray] = []

    def reset(self):
        self._loud = self._quiet = 0
        self._active = False
        self._buf = []

    def feed(self, frame: np.ndarray):
        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))
        if rms > RMS_THRESH:
            self._loud += 1; self._quiet = 0
        else:
            self._quiet += 1; self._loud = 0
        if not self._active:
            if self._loud >= START_FRAMES:
                self._active = True; self._buf = []
                return "start", rms
        else:
            self._buf.append(frame.copy())
            if self._quiet >= END_FRAMES:
                frames = list(self._buf); self._buf = []; self._active = False
                return "end", frames
            return "frame", rms
        return None, rms

# ── STT ───────────────────────────────────────────────────────────────────────

# ── STT ───────────────────────────────────────────────────────────────────────

_stt_failure_until: float = 0.0   # cooldown timestamp after all providers fail
_faster_whisper_model = None       # lazy-loaded once

async def transcribe(frames: list[np.ndarray]) -> str:
    global _stt_failure_until, _faster_whisper_model
    import time

    # If all providers recently failed, skip until cooldown expires
    if time.time() < _stt_failure_until:
        return ""

    audio = np.concatenate(frames, axis=0)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wavfile.write(f.name, SR, audio)
        path = f.name

    loop = asyncio.get_event_loop()

    async def _try_elevenlabs():
        api_11 = _load_key("elevenlabs", "ELEVENLABS_API_KEY")
        if not api_11: return None
        try:
            el = ElevenLabs(api_key=api_11)
            def _eleven():
                with open(path, "rb") as fh:
                    return el.speech_to_text.convert(
                        file=fh, model_id="scribe_v1",
                        tag_audio_events=False, timestamps_granularity="none",
                    ).text.strip()
            result = await loop.run_in_executor(None, _eleven)
            write_log("stt/elevenlabs", result[:150])
            return result
        except Exception as e:
            print(f"[stt] ElevenLabs: {str(e)[:80]}")
            return None

    async def _try_groq():
        groq_key = _load_key("groq", "GROQ_API_KEY")
        if not groq_key: return None
        try:
            import openai as _oai
            client = _oai.OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            def _groq_stt():
                with open(path, "rb") as fh:
                    return client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo", file=fh
                    ).text.strip()
            result = await loop.run_in_executor(None, _groq_stt)
            write_log("stt/groq", result[:150])
            return result
        except Exception as e:
            print(f"[stt] Groq: {str(e)[:60]}")
            return None

    async def _try_local():
        # Must use global keyword here because we assign to _faster_whisper_model
        global _faster_whisper_model
        try:
            from faster_whisper import WhisperModel  # type: ignore
            if _faster_whisper_model is None:
                print("[stt] Loading local faster-whisper tiny model…")
                _faster_whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            wm = _faster_whisper_model
            def _local():
                segs, _ = wm.transcribe(path, beam_size=1, language="en")
                return " ".join(s.text for s in segs).strip()
            result = await loop.run_in_executor(None, _local)
            write_log("stt/local", result[:150])
            return result
        except Exception as e:
            print(f"[stt] local whisper: {str(e)[:80]}")
            return None

    try:
        result = None
        if preferred_stt == "elevenlabs":
            result = await _try_elevenlabs()
        elif preferred_stt == "groq":
            result = await _try_groq()
        elif preferred_stt == "local":
            result = await _try_local()
        else:  # "auto" — full fallback chain
            result = await _try_elevenlabs()
            if result is None:
                result = await _try_groq()
            if result is None:
                result = await _try_local()

        if result is not None:
            return result

        # All failed — impose 30s cooldown to prevent hammering
        print("[stt] All STT providers failed. Pausing voice input for 30s. Use text input instead.")
        await broadcast({"type": "transcript", "role": "system",
                         "text": "⚠️ Voice recognition failed (check mic/faster-whisper). Using text input."})
        _stt_failure_until = time.time() + 30.0
        return ""

    finally:
        try:
            os.unlink(path)
        except Exception:
            pass

# ── Operator tools ────────────────────────────────────────────────────────────

# Playwright browser singleton
_pw_browser = None
_pw_page    = None

async def get_browser_page():
    """Lazy-init a persistent Playwright Chromium browser page."""
    global _pw_browser, _pw_page
    try:
        from playwright.async_api import async_playwright
        if _pw_browser is None:
            _pw = await async_playwright().start()
            _pw_browser = await _pw.chromium.launch(headless=False, args=["--start-maximized"])
        if _pw_page is None or _pw_page.is_closed():
            _pw_page = await _pw_browser.new_page()
        return _pw_page
    except Exception as e:
        print(f"[playwright] {e}")
        return None

TOOLS = [
    # ── Screen & vision
    {"type":"function","function":{"name":"read_screen","description":"Take a screenshot and OCR all visible text on the desktop. Always call this first to locate UI elements before clicking.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"screenshot","description":"Take a screenshot and return it to the user without OCR. Use to see current state of screen.","parameters":{"type":"object","properties":{},"required":[]}}},
    # ── Mouse control
    {"type":"function","function":{"name":"click","description":"Click at pixel coordinates on screen.","parameters":{"type":"object","properties":{"x":{"type":"integer","description":"X pixel coordinate"},"y":{"type":"integer","description":"Y pixel coordinate"},"button":{"type":"string","enum":["left","right","middle"],"description":"Mouse button"}},"required":["x","y"]}}},
    {"type":"function","function":{"name":"double_click","description":"Double-click at pixel coordinates (e.g. to open files/apps).","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"}},"required":["x","y"]}}},
    {"type":"function","function":{"name":"right_click","description":"Right-click at coordinates to open context menus.","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"}},"required":["x","y"]}}},
    {"type":"function","function":{"name":"move_mouse","description":"Move mouse to coordinates without clicking (hover).","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"}},"required":["x","y"]}}},
    {"type":"function","function":{"name":"drag","description":"Click and drag from one position to another.","parameters":{"type":"object","properties":{"x1":{"type":"integer"},"y1":{"type":"integer"},"x2":{"type":"integer"},"y2":{"type":"integer"}},"required":["x1","y1","x2","y2"]}}},
    {"type":"function","function":{"name":"scroll","description":"Scroll mouse wheel at coordinates.","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"},"direction":{"type":"string","enum":["up","down"]},"clicks":{"type":"integer","description":"Number of scroll clicks, default 3"}},"required":["x","y","direction"]}}},
    # ── Keyboard
    {"type":"function","function":{"name":"type_text","description":"Type text at current keyboard focus. Use for filling forms, search boxes, etc.","parameters":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}}},
    {"type":"function","function":{"name":"press_key","description":"Press a key or keyboard shortcut. Examples: 'enter', 'escape', 'ctrl+c', 'ctrl+v', 'alt+tab', 'win+r', 'ctrl+shift+t'.","parameters":{"type":"object","properties":{"key":{"type":"string"}},"required":["key"]}}},
    # ── Clipboard
    {"type":"function","function":{"name":"get_clipboard","description":"Get text currently in the clipboard.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"set_clipboard","description":"Copy text to the clipboard.","parameters":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}}},
    # ── Windows
    {"type":"function","function":{"name":"list_windows","description":"List all open application windows with their titles.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"focus_window","description":"Bring a window to the foreground by its title (partial match ok).","parameters":{"type":"object","properties":{"title":{"type":"string"}},"required":["title"]}}},
    # ── Shell
    {"type":"function","function":{"name":"run_command","description":"Run a Windows shell command and return output. Use to open apps (start chrome), manage files, query system info.","parameters":{"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}}},
    # ── File system
    {"type":"function","function":{"name":"read_file","description":"Read the contents of a file.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"write_file","description":"Write content to a file (creates or overwrites).","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},
    {"type":"function","function":{"name":"list_files","description":"List files and folders in a directory.","parameters":{"type":"object","properties":{"path":{"type":"string","description":"Directory path, defaults to Desktop"}},"required":[]}}},
    # ── Browser (Playwright)
    {"type":"function","function":{"name":"browser_open","description":"Open a URL in the controlled Chromium browser.","parameters":{"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}}},
    {"type":"function","function":{"name":"browser_click","description":"Click an element in the browser by CSS selector or text.","parameters":{"type":"object","properties":{"selector":{"type":"string","description":"CSS selector, XPath, or visible text to click"}},"required":["selector"]}}},
    {"type":"function","function":{"name":"browser_fill","description":"Fill a form field in the browser.","parameters":{"type":"object","properties":{"selector":{"type":"string"},"text":{"type":"string"}},"required":["selector","text"]}}},
    {"type":"function","function":{"name":"browser_extract","description":"Extract visible text content from the browser page or a specific element.","parameters":{"type":"object","properties":{"selector":{"type":"string","description":"CSS selector to extract from, or empty for full page"}},"required":[]}}},
    {"type":"function","function":{"name":"browser_screenshot","description":"Take a screenshot of the current browser page.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"browser_press","description":"Press a key in the browser (e.g. Enter, Tab, Escape).","parameters":{"type":"object","properties":{"key":{"type":"string"}},"required":["key"]}}},
]

# Tool name → description map for Ollama prompt injection
TOOL_DESCRIPTIONS = "\n".join(
    f"  {t['function']['name']}: {t['function']['description']}"
    for t in TOOLS
)

async def exec_tool(name: str, args: dict) -> str:
    loop = asyncio.get_event_loop()

    # ── Screen & vision ────────────────────────────────────────────────────────
    if name in ("read_screen", "screenshot"):
        def _snap():
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=55)
            return base64.b64encode(buf.getvalue()).decode(), img
        snap_b64, img = await loop.run_in_executor(None, _snap)
        await broadcast({"type": "screenshot", "data": snap_b64})
        if name == "read_screen":
            if HAS_OCR:
                import pytesseract
                text = await loop.run_in_executor(None, lambda: pytesseract.image_to_string(img).strip())
                return text[:2000] if text else "(screen appears blank)"
            return "(OCR unavailable — screenshot sent to UI)"
        return "(screenshot captured)"

    # ── Mouse ──────────────────────────────────────────────────────────────────
    elif name == "click":
        x, y, btn = args.get("x", 0), args.get("y", 0), args.get("button", "left")
        await loop.run_in_executor(None, lambda: pyautogui.click(x, y, button=btn))
        return f"Clicked {btn} at ({x},{y})"
    elif name == "double_click":
        x, y = args.get("x", 0), args.get("y", 0)
        await loop.run_in_executor(None, lambda: pyautogui.doubleClick(x, y))
        return f"Double-clicked at ({x},{y})"
    elif name == "right_click":
        x, y = args.get("x", 0), args.get("y", 0)
        await loop.run_in_executor(None, lambda: pyautogui.rightClick(x, y))
        return f"Right-clicked at ({x},{y})"
    elif name == "move_mouse":
        x, y = args.get("x", 0), args.get("y", 0)
        await loop.run_in_executor(None, lambda: pyautogui.moveTo(x, y, duration=0.3))
        return f"Mouse moved to ({x},{y})"
    elif name == "drag":
        x1,y1,x2,y2 = args.get("x1",0),args.get("y1",0),args.get("x2",0),args.get("y2",0)
        await loop.run_in_executor(None, lambda: pyautogui.drag(x2-x1, y2-y1, duration=0.4, button="left"))
        return f"Dragged from ({x1},{y1}) to ({x2},{y2})"
    elif name == "scroll":
        x, y = args.get("x", 0), args.get("y", 0)
        dir_ = args.get("direction", "down")
        clicks = args.get("clicks", 3)
        amount = clicks if dir_ == "up" else -clicks
        await loop.run_in_executor(None, lambda: pyautogui.scroll(amount, x=x, y=y))
        return f"Scrolled {dir_} {clicks} clicks at ({x},{y})"

    # ── Keyboard ───────────────────────────────────────────────────────────────
    elif name == "type_text":
        text = args.get("text", "")
        await loop.run_in_executor(None, lambda: pyautogui.write(text, interval=0.03))
        return f"Typed: {text[:80]}"
    elif name == "press_key":
        key = args.get("key", "")
        parts = [p.strip() for p in key.lower().split("+")]
        await loop.run_in_executor(None, lambda: pyautogui.hotkey(*parts))
        return f"Pressed: {key}"

    # ── Clipboard ──────────────────────────────────────────────────────────────
    elif name == "get_clipboard":
        try:
            import pyperclip
            return pyperclip.paste() or "(clipboard empty)"
        except Exception as e:
            return f"Clipboard error: {e}"
    elif name == "set_clipboard":
        text = args.get("text", "")
        try:
            import pyperclip
            pyperclip.copy(text)
            return f"Copied to clipboard: {text[:60]}"
        except Exception as e:
            return f"Clipboard error: {e}"

    # ── Windows ────────────────────────────────────────────────────────────────
    elif name == "list_windows":
        try:
            import pygetwindow as gw
            wins = [w.title for w in gw.getAllWindows() if w.title.strip()]
            return "\n".join(wins[:30]) if wins else "(no windows found)"
        except Exception as e:
            return f"Error: {e}"
    elif name == "focus_window":
        title = args.get("title", "")
        try:
            import pygetwindow as gw
            wins = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
            if wins:
                wins[0].activate()
                await asyncio.sleep(0.3)
                return f"Focused: {wins[0].title}"
            return f"No window matching '{title}' found"
        except Exception as e:
            return f"Error: {e}"

    # ── Shell ──────────────────────────────────────────────────────────────────
    elif name == "run_command":
        cmd = args.get("command", "")
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, err = await asyncio.wait_for(proc.communicate(), timeout=20)
            result = (out + err).decode(errors="replace").strip()
            return result[:1500] if result else "(no output)"
        except asyncio.TimeoutError:
            return "Command timed out (20s)"
        except Exception as e:
            return f"Error: {e}"

    # ── File system ────────────────────────────────────────────────────────────
    elif name == "read_file":
        path = args.get("path", "")
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            return content[:3000] if content else "(empty file)"
        except Exception as e:
            return f"Error reading file: {e}"
    elif name == "write_file":
        path, content = args.get("path", ""), args.get("content", "")
        try:
            Path(path).write_text(content, encoding="utf-8")
            return f"Written {len(content)} chars to {path}"
        except Exception as e:
            return f"Error writing file: {e}"
    elif name == "list_files":
        raw = args.get("path", "")
        if not raw:
            # Resolve real Desktop path (works with OneDrive-redirected desktops)
            try:
                import winreg
                _k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                raw, _ = winreg.QueryValueEx(_k, "Desktop")
            except Exception:
                raw = str(Path.home() / "Desktop")
        try:
            items = list(Path(raw).iterdir())
            lines = [f"{'[DIR] ' if i.is_dir() else '      '}{i.name}" for i in sorted(items)[:50]]
            return "\n".join(lines) if lines else "(empty directory)"
        except Exception as e:
            return f"Error: {e}"

    # ── Browser (Playwright) ───────────────────────────────────────────────────
    elif name == "browser_open":
        url = args.get("url", "")
        page = await get_browser_page()
        if page is None:
            return "Browser unavailable — is Playwright installed?"
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        return f"Opened: {url}"
    elif name == "browser_click":
        selector = args.get("selector", "")
        page = await get_browser_page()
        if page is None: return "Browser unavailable"
        try:
            # Try CSS selector first, then text match
            try:
                await page.click(selector, timeout=5000)
            except Exception:
                await page.get_by_text(selector).first.click(timeout=5000)
            return f"Clicked: {selector}"
        except Exception as e:
            return f"Click failed: {e}"
    elif name == "browser_fill":
        selector, text = args.get("selector", ""), args.get("text", "")
        page = await get_browser_page()
        if page is None: return "Browser unavailable"
        try:
            await page.fill(selector, text, timeout=5000)
            return f"Filled '{selector}' with: {text[:60]}"
        except Exception as e:
            return f"Fill failed: {e}"
    elif name == "browser_extract":
        selector = args.get("selector", "")
        page = await get_browser_page()
        if page is None: return "Browser unavailable"
        try:
            if selector:
                text = await page.inner_text(selector, timeout=5000)
            else:
                text = await page.inner_text("body", timeout=5000)
            return text.strip()[:3000]
        except Exception as e:
            return f"Extract failed: {e}"
    elif name == "browser_screenshot":
        page = await get_browser_page()
        if page is None: return "Browser unavailable"
        buf = await page.screenshot()
        b64 = base64.b64encode(buf).decode()
        await broadcast({"type": "screenshot", "data": b64})
        return "(browser screenshot sent to Vision tab)"
    elif name == "browser_press":
        key = args.get("key", "Enter")
        page = await get_browser_page()
        if page is None: return "Browser unavailable"
        await page.keyboard.press(key)
        return f"Browser pressed: {key}"

    return f"Unknown tool: {name}"

# ── LLM ───────────────────────────────────────────────────────────────────────

# Models known to support native function calling
_NATIVE_TOOL_MODELS = {
    "openai", "github", "groq", "deepseek", "mistral", "gemini"
}
# Ollama model families that support native tool calling
_OLLAMA_TOOL_FAMILIES = {
    "llama3.1", "llama3.2", "llama3.3", "llama3.4", "qwen2.5", "qwen2", "qwen3",
    "mistral-nemo", "mixtral", "firefunction", "functionary", "nexusraven", "gorilla",
    "command-r", "phi3", "phi4", "smollm2", "gemma3", "gemma2",
}

def _model_supports_tools() -> bool:
    """Return True if the current provider/model supports native function calling."""
    if current_provider != "ollama":
        return current_provider in _NATIVE_TOOL_MODELS
    m = current_model.lower()
    if any(m.startswith(f) for f in _OLLAMA_TOOL_FAMILIES):
        return True
    # Try native tools for ALL Ollama models — Ollama supports JSON tool calling
    # broadly. llm_stream catches errors and falls back to prompt-based.
    return True

# Regex to parse prompt-based tool calls from Ollama models that don't support native FC
import re as _re

# Matches: TOOL_CALL: run_command(...) OR bare run_command(...)
# Also handles transcription-spaced variants: run _command  read _screen
_TOOL_NAMES_PATTERN = (
    r'run_?\s*command|read_?\s*screen|screenshot|double_?\s*click|right_?\s*click|click|'
    r'type_?\s*text|press_?\s*key|get_?\s*clipboard|set_?\s*clipboard|list_?\s*windows|'
    r'focus_?\s*window|read_?\s*file|write_?\s*file|list_?\s*files|'
    r'browser_?\s*open|browser_?\s*click|browser_?\s*fill|browser_?\s*extract|'
    r'browser_?\s*screenshot|browser_?\s*press|move_?\s*mouse|drag|scroll'
)
_BARE_TOOL_RE = _re.compile(
    r'(?:TOOL_CALL:\s*)?(?P<name>' + _TOOL_NAMES_PATTERN + r')\s*\((?P<args>[^)]*)\)',
    _re.IGNORECASE
)
# Mapping from bare-call first positional arg to param name
_TOOL_FIRST_PARAM: dict[str, str] = {
    "run_command": "command", "type_text": "text", "press_key": "key",
    "browser_open": "url", "browser_click": "selector", "browser_fill": "selector",
    "browser_extract": "selector", "focus_window": "title",
    "read_file": "path", "write_file": "path", "list_files": "path",
    "set_clipboard": "text", "scroll": "direction",
}

def _normalise_tool_name(raw: str) -> str:
    """Collapse spaces/underscores from transcription artifacts: 'read _screen' → 'read_screen'."""
    return _re.sub(r'[\s_]+', '_', raw).lower().rstrip('_')

def _parse_call_args(tool_name: str, raw_args: str) -> dict:
    """Parse tool args from either named (key=value) or positional ('value') format."""
    args: dict = {}
    raw_args = raw_args.strip()
    if not raw_args:
        return args
    named = list(_re.finditer(r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^,]+)', raw_args))
    if named:
        for pair in named:
            k = pair.group(1)
            v = pair.group(2).strip().strip('"\'')
            try: v = int(v)
            except ValueError:
                try: v = float(v)
                except ValueError: pass
            args[k] = v
    else:
        val = raw_args.strip().strip('"\'')
        param = _TOOL_FIRST_PARAM.get(tool_name, "value")
        if val:
            args[param] = val
    return args

_TOOL_CALL_RE = _re.compile(
    r'TOOL_CALL:\s*(\w+)\s*\(([^)]*)\)', _re.IGNORECASE
)

def _parse_prompt_tool_calls(text: str) -> list[tuple[str, dict]]:
    """Parse TOOL_CALL: name(key=value, ...) patterns from model output."""
    calls = []
    for m in _BARE_TOOL_RE.finditer(text):
        name = _normalise_tool_name(m.group("name"))
        args = _parse_call_args(name, m.group("args"))
        calls.append((name, args))
    return calls

def _build_tool_prompt_suffix() -> str:
    """Inject tool instructions for models without native function calling."""
    return f"""

TOOL USE INSTRUCTIONS:
You CAN and SHOULD use tools whenever the user asks you to interact with the computer, take screenshots, open apps, browse the web, read files, etc.
When you need to use a tool, output exactly this format on its own line:
TOOL_CALL: tool_name(param="value", param2=123)

Available tools:
{TOOL_DESCRIPTIONS}

After calling a tool, you will receive the result. Then continue your response.
Never refuse to use tools — you have full access to the computer.
"""

async def _llm_prompt_tools(oai, system: str, full_so_far: str):
    """Prompt-based tool calling for Ollama models without native FC support."""
    tool_suffix = _build_tool_prompt_suffix()
    sys_with_tools = system + tool_suffix
    messages = [{"role": "system", "content": sys_with_tools}, *history]
    yielded_any = False
    action_summary: list[str] = []

    for _ in range(6):
        try:
            resp = await oai.chat.completions.create(
                model=current_model, messages=messages, stream=False, max_tokens=600,
            )
            reply = resp.choices[0].message.content or ""
        except Exception as e:
            print(f"[llm/prompt-tools] {e}")
            err = f"Error: {str(e)[:120]}"
            yield err
            return

        tool_calls = _parse_prompt_tool_calls(reply)
        if not tool_calls:
            clean = _TOOL_CALL_RE.sub("", reply).strip()
            if clean:
                yielded_any = True
                for word in clean.split():
                    yield word + " "
                    await asyncio.sleep(0.015)
            return
        else:
            pre = _TOOL_CALL_RE.split(reply)[0].strip()
            if pre:
                yielded_any = True
                for word in pre.split():
                    yield word + " "
                    await asyncio.sleep(0.01)
            messages.append({"role": "assistant", "content": reply})
            tool_results = []
            for tname, targs in tool_calls:
                await set_state("thinking")
                result = await exec_tool(tname, targs)
                await broadcast_action(tname, targs, result)
                action_summary.append(f"{tname}: {result[:80]}")
                tool_results.append(f"[{tname}] → {result}")
            messages.append({"role": "user", "content": "Tool results:\n" + "\n".join(tool_results) + "\n\nNow give a brief spoken reply summarizing what you did."})

    # If no text was ever yielded, synthesize a short summary
    if not yielded_any and action_summary:
        summary = "Done. " + "; ".join(action_summary[:3])
        for word in summary.split():
            yield word + " "
            await asyncio.sleep(0.015)



# ── OpenAI Responses API (computer-use-preview + streaming tool loop) ─────────

_RESPONSES_API_MODELS = {"computer-use-preview", "gpt-4.1", "gpt-4.1-mini", "o4-mini", "o3"}

def _use_responses_api() -> bool:
    """True when OpenAI provider + model supports the Responses API."""
    return current_provider == "openai" and current_model in _RESPONSES_API_MODELS


async def _take_screenshot_b64() -> str:
    """Take a desktop screenshot and return base64 JPEG."""
    loop = asyncio.get_event_loop()
    def _snap():
        img = pyautogui.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    b64 = await loop.run_in_executor(None, _snap)
    await broadcast({"type": "screenshot", "data": b64})
    return b64


async def _execute_computer_action(action) -> dict:
    """Execute a computer_call action and return the screenshot output dict."""
    loop = asyncio.get_event_loop()
    action_type = getattr(action, "type", "screenshot")

    if action_type == "screenshot":
        pass  # Just take a screenshot below

    elif action_type == "click":
        x, y = int(action.x), int(action.y)
        button = getattr(action, "button", "left")
        btn_map = {"left": "left", "right": "right", "middle": "middle", "wheel": "middle", "back": "left", "forward": "left"}
        btn = btn_map.get(str(button).lower(), "left")
        await loop.run_in_executor(None, lambda: pyautogui.click(x, y, button=btn))

    elif action_type == "double_click":
        x, y = int(action.x), int(action.y)
        await loop.run_in_executor(None, lambda: pyautogui.doubleClick(x, y))

    elif action_type == "right_click":
        x, y = int(action.x), int(action.y)
        await loop.run_in_executor(None, lambda: pyautogui.rightClick(x, y))

    elif action_type == "scroll":
        x, y = int(action.x), int(action.y)
        dx = getattr(action, "scroll_x", 0) or getattr(action, "delta_x", 0)
        dy = getattr(action, "scroll_y", 0) or getattr(action, "delta_y", 0)
        if dy:
            await loop.run_in_executor(None, lambda: pyautogui.scroll(int(dy), x=x, y=y))

    elif action_type == "type":
        text = getattr(action, "text", "")
        await loop.run_in_executor(None, lambda: pyautogui.write(text, interval=0.03))

    elif action_type == "key":
        keys = getattr(action, "key", "") or getattr(action, "keys", "")
        if keys:
            parts = [p.strip().lower() for p in str(keys).replace("+", " ").split()]
            if len(parts) > 1:
                await loop.run_in_executor(None, lambda: pyautogui.hotkey(*parts))
            else:
                await loop.run_in_executor(None, lambda: pyautogui.press(parts[0]))

    elif action_type == "move":
        x, y = int(action.x), int(action.y)
        await loop.run_in_executor(None, lambda: pyautogui.moveTo(x, y, duration=0.2))

    elif action_type == "drag":
        x, y = int(action.x), int(action.y)
        ex, ey = int(action.end_x), int(action.end_y)
        await loop.run_in_executor(None, lambda: (
            pyautogui.mouseDown(x, y), pyautogui.moveTo(ex, ey, duration=0.4), pyautogui.mouseUp()
        ))

    elif action_type in ("wait", "pause"):
        await asyncio.sleep(1.0)

    # Always return a fresh screenshot showing current state
    b64 = await _take_screenshot_b64()
    return {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"}


async def _llm_stream_responses_api(user_text: str):
    """
    OpenAI Responses API streaming path.
    - computer-use-preview: native computer_use_preview tool loop
    - other Responses API models: function tool calling via Responses API
    Yields text tokens as an async generator.
    """
    from openai import AsyncOpenAI as _AsyncOpenAI
    api_key = PROVIDERS["openai"]["api_key"]
    if not api_key:
        yield "OpenAI API key not configured. Add it in ⚙ Settings."
        return

    oai = _AsyncOpenAI(api_key=api_key, timeout=120.0)
    screen_w, screen_h = pyautogui.size()
    is_cua = current_model == "computer-use-preview"
    system = build_system_prompt()
    full   = ""
    actions_taken: list[str] = []

    # Build initial input from history (skip system messages, last 14 turns)
    input_items: list[dict] = []
    for msg in history[-14:]:
        role = msg.get("role", "user")
        content = msg.get("content") or ""
        if role in ("user", "assistant") and content:
            input_items.append({"role": role, "content": content})
    input_items.append({"role": "user", "content": user_text})

    # Tool definitions
    if is_cua:
        tools: list[dict] = [{
            "type": "computer_use_preview",
            "display_width":  screen_w,
            "display_height": screen_h,
            "environment":    "windows",
        }]
    else:
        # Convert existing Chat-Completions TOOLS to Responses API format
        tools = [
            {
                "type":        "function",
                "name":        t["function"]["name"],
                "description": t["function"].get("description", ""),
                "parameters":  t["function"].get("parameters", {}),
                "strict":      False,
            }
            for t in TOOLS
        ]

    # ── Initial API call ───────────────────────────────────────────────────────
    try:
        create_kwargs: dict = dict(
            model=current_model,
            tools=tools,
            input=input_items,
            instructions=system,
            truncation="auto",
        )
        if is_cua:
            create_kwargs["reasoning"] = {"effort": "high", "summary": "concise"}
        response = await oai.responses.create(**create_kwargs)
    except Exception as e:
        err = f"Error: {str(e)[:160]}"
        yield err
        return

    # ── Response→action loop ───────────────────────────────────────────────────
    MAX_ROUNDS = 12
    round_num  = 0

    while round_num < MAX_ROUNDS:
        round_num += 1

        # Extract any text content
        for item in getattr(response, "output", []):
            if getattr(item, "type", "") == "message":
                for block in getattr(item, "content", []):
                    text = getattr(block, "text", None)
                    if text:
                        for word in text.split():
                            yield word + " "
                            full += word + " "
                            await asyncio.sleep(0.012)

        # Check for pending computer_call items
        if is_cua:
            computer_calls = [
                i for i in getattr(response, "output", [])
                if getattr(i, "type", "") == "computer_call"
            ]
            if not computer_calls:
                break

            tool_outputs: list[dict] = []
            for cc in computer_calls:
                action = getattr(cc, "action", None)
                call_id = getattr(cc, "call_id", None)
                atype = getattr(action, "type", "screenshot")
                await set_state("thinking")
                output = await _execute_computer_action(action)
                await broadcast_action(atype, {}, f"computer_call: {atype}")
                actions_taken.append(atype)
                tool_outputs.append({
                    "type":    "computer_call_output",
                    "call_id": call_id,
                    "output":  output,
                })

            # Safety check for pending_safety_checks
            safety = getattr(response, "output", [])
            for item in safety:
                for sc in getattr(item, "pending_safety_checks", []):
                    tool_outputs.append({
                        "type":    "input_item",
                        "item":    {"type": "safety_check_acknowledgement", "id": getattr(sc, "id", "")},
                    })

            try:
                response = await oai.responses.create(
                    model=current_model,
                    tools=tools,
                    input=tool_outputs,
                    previous_response_id=response.id,
                    truncation="auto",
                )
            except Exception as e:
                yield f" [tool error: {str(e)[:80]}]"
                break

        else:
            # Responses API function calling (non-CUA models)
            function_calls = [
                i for i in getattr(response, "output", [])
                if getattr(i, "type", "") == "function_call"
            ]
            if not function_calls:
                break

            fn_outputs: list[dict] = []
            for fc in function_calls:
                name    = getattr(fc, "name", "")
                call_id = getattr(fc, "call_id", None)
                try:
                    args = json.loads(getattr(fc, "arguments", "{}") or "{}")
                except Exception:
                    args = {}
                await set_state("thinking")
                result = await exec_tool(name, args)
                await broadcast_action(name, args, result)
                actions_taken.append(f"{name}: {result[:60]}")
                fn_outputs.append({
                    "type":    "function_call_output",
                    "call_id": call_id,
                    "output":  result,
                })

            # Force a text reply after tools
            fn_outputs.append({
                "role":    "user",
                "content": "You just used tools. Give a brief 1-2 sentence spoken reply summarising what you did.",
            })
            try:
                response = await oai.responses.create(
                    model=current_model,
                    tools=[],
                    input=fn_outputs,
                    previous_response_id=response.id,
                    truncation="auto",
                )
            except Exception as e:
                yield f" [tool error: {str(e)[:80]}]"
                break

    # Synthesise a fallback if no text was produced
    if not full.strip() and actions_taken:
        text = "Done — " + "; ".join(actions_taken[:3]) + "."
        for word in text.split():
            yield word + " "
            full += word + " "
            await asyncio.sleep(0.015)

    if full:
        history.append({"role": "assistant", "content": full})
        # NOTE: add_transcript is called by speak() — don't call here to avoid duplicate
    write_log("llm_responses", full[:150])


_THINKING_PREFIXES = ("deepseek-r1", "qwen3", "qwq", "marco-o1")

def _is_thinking_model() -> bool:
    m = current_model.lower()
    return any(m.startswith(t) for t in _THINKING_PREFIXES)


async def _llm_stream_ollama(user_text: str):
    """
    Native ollama.AsyncClient streaming with:
    - OllamaOptions typed parameters
    - think=True for reasoning models (deepseek-r1, qwen3, qwq)
    - Native tool calling with fallback to prompt-based
    - OllamaResponseError handling
    """
    client = get_ollama_client()
    system = build_system_prompt()
    think  = _is_thinking_model()
    full   = ""
    actions_taken: list[str] = []

    options = OllamaOptions(
        temperature=0.7,
        top_k=40,
        top_p=0.9,
        num_ctx=4096,
    )

    msgs: list[dict] = [{"role": "system", "content": system}, *history[-20:]]
    tools_to_use = TOOLS if mode == "operator" else []

    for _round in range(6):
        tool_calls_pending: list = []
        chunk_text = ""
        try:
            kwargs: dict = dict(
                model=current_model,
                messages=msgs,
                stream=True,
                tools=tools_to_use,
                options=options,
            )
            if think:
                kwargs["think"] = True

            async for chunk in await client.chat(**kwargs):
                msg = chunk.message

                # Broadcast reasoning/thinking tokens
                if think and getattr(msg, "thinking", None):
                    await broadcast({"type": "thinking", "text": msg.thinking})

                # Accumulate tool calls (native FC)
                if getattr(msg, "tool_calls", None):
                    tool_calls_pending.extend(msg.tool_calls)

                # Stream text — in operator mode we buffer (don't yield yet) so we
                # can intercept bare function calls before they get spoken aloud.
                if msg.content:
                    chunk_text += msg.content
                    if mode != "operator":
                        for word in msg.content.split():
                            yield word + " "
                            full += word + " "
                            await asyncio.sleep(0.012)

                if chunk.done:
                    break

        except OllamaResponseError as e:
            # Native tool calling not supported — fall back to prompt-based
            if "tool" in str(e.error).lower() or "function" in str(e.error).lower():
                print(f"[llm/ollama] tool error → prompt fallback: {e.error}")
                oai = get_oai_client()
                async for c in _llm_prompt_tools(oai, system, full):
                    full += c; yield c
                break
            yield f"Ollama error: {e.error}"
            break
        except Exception as e:
            print(f"[llm/ollama] {e}")
            yield f"Error: {str(e)[:120]}"
            break

        # --- Operator mode: detect bare text tool calls (qwen3, llama3.1, etc.) ---
        if mode == "operator" and not tool_calls_pending and chunk_text:
            bare_calls = _parse_prompt_tool_calls(chunk_text)
            if bare_calls:
                # Strip the tool call lines from the response text
                clean_text = _BARE_TOOL_RE.sub("", chunk_text).strip()
                # Yield only the human-readable preamble
                if clean_text:
                    for word in clean_text.split():
                        yield word + " "
                        full += word + " "
                        await asyncio.sleep(0.012)
                # Execute each bare tool call
                msgs.append({"role": "assistant", "content": chunk_text})
                for tool_name, args in bare_calls:
                    await set_state("thinking")
                    result = await exec_tool(tool_name, args)
                    await broadcast_action(tool_name, args, result)
                    actions_taken.append(f"{tool_name}: {result[:60]}")
                    msgs.append({"role": "tool", "content": result})
                msgs.append({"role": "user",
                             "content": "Tool done. One short sentence summary."})
                continue  # go to next round for follow-up

        # In operator mode with no tool calls, flush buffered text now
        if mode == "operator" and chunk_text and not tool_calls_pending:
            for word in chunk_text.split():
                yield word + " "
                full += word + " "
                await asyncio.sleep(0.012)

        if not tool_calls_pending:
            break

        # Execute tool calls
        msgs.append({"role": "assistant", "content": chunk_text,
                     "tool_calls": tool_calls_pending})
        for tc in tool_calls_pending:
            name = tc.function.name
            args = tc.function.arguments if isinstance(tc.function.arguments, dict) \
                   else json.loads(getattr(tc.function, "arguments", "{}") or "{}")
            await set_state("thinking")
            result = await exec_tool(name, args)
            await broadcast_action(name, args, result)
            actions_taken.append(f"{name}: {result[:60]}")
            msgs.append({"role": "tool", "content": result})
        msgs.append({"role": "user",
                     "content": "Tools executed. Give a brief spoken summary."})

    if full.strip():
        history.append({"role": "assistant", "content": full.strip()})
        # NOTE: add_transcript is called by speak() — don't call here to avoid duplicate
    elif actions_taken:
        summary = "Done — " + "; ".join(a.split(":")[0] for a in actions_taken[:3]) + "."
        for word in summary.split():
            yield word + " "
            await asyncio.sleep(0.015)
    write_log("llm/ollama", full[:150])


async def _llm_stream_openai(user_text: str):
    """
    Streaming Chat Completions for OpenAI-compatible providers.
    Catches specific openai exceptions and streams tokens live.
    """
    oai    = get_oai_client()
    system = build_system_prompt()
    full   = ""
    actions_taken: list[str] = []

    MAX_TOOL_ROUNDS = 1
    tool_rounds     = 0

    while True:
        force_text = tool_rounds >= MAX_TOOL_ROUNDS
        base_msgs  = [{"role": "system", "content": system}, *history]
        if force_text and actions_taken:
            base_msgs.append({
                "role": "user",
                "content": "Tools done. Give a brief 1-2 sentence spoken reply.",
            })
        kw_tools = {} if force_text else {"tools": TOOLS, "tool_choice": "auto"}

        try:
            stream = await oai.chat.completions.create(
                model=current_model,
                messages=base_msgs,
                max_tokens=600,
                stream=True,
                **kw_tools,
            )

            chunk_text = ""
            tool_calls_acc: dict[int, dict] = {}
            finish_reason: str | None = None

            async for chunk in stream:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                finish_reason = choice.finish_reason or finish_reason
                delta = choice.delta

                # Accumulate streaming tool call fragments
                for tc_delta in (delta.tool_calls or []):
                    idx = tc_delta.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.id:
                        tool_calls_acc[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_acc[idx]["name"] += tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_acc[idx]["arguments"] += tc_delta.function.arguments

                if delta.content:
                    chunk_text += delta.content
                    for word in delta.content.split():
                        yield word + " "
                        full += word + " "
                        await asyncio.sleep(0.012)

        except openai.RateLimitError:
            yield "Rate limit reached — please wait a moment."; break
        except openai.APIStatusError as e:
            yield f"API error {e.status_code}: {str(e.message)[:100]}"; break
        except openai.APIConnectionError:
            yield "Connection error — check your internet."; break
        except openai.APITimeoutError:
            yield "Request timed out."; break
        except Exception as e:
            err_s = str(e)
            print(f"[llm/openai] {err_s[:120]}")
            if any(k in err_s.lower() for k in ("tool", "function", "schema", "unsupported")):
                async for c in _llm_prompt_tools(oai, system, full):
                    full += c; yield c
            else:
                yield f"Error: {err_s[:120]}"
            break

        if finish_reason == "tool_calls" and not force_text:
            tool_rounds += 1
            tcs = list(tool_calls_acc.values())
            history.append({
                "role": "assistant", "content": None,
                "tool_calls": [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                    for tc in tcs
                ],
            })
            for tc in tcs:
                try:
                    args = json.loads(tc["arguments"] or "{}")
                except Exception:
                    args = {}
                await set_state("thinking")
                result = await exec_tool(tc["name"], args)
                await broadcast_action(tc["name"], args, result)
                actions_taken.append(f"{tc['name']}: {result[:60]}")
                history.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            continue  # next iteration forces text reply
        else:
            if not chunk_text and actions_taken:
                chunk_text = "Done — " + "; ".join(a.split(":")[0] for a in actions_taken[:3]) + "."
                for word in chunk_text.split():
                    yield word + " "
                    full += word + " "
                    await asyncio.sleep(0.015)
            break

    if full.strip():
        history.append({"role": "assistant", "content": full.strip()})
        # NOTE: add_transcript is called by speak() — don't call here to avoid duplicate
    write_log("llm/openai", full[:150])


async def llm_stream(user_text: str):
    """
    Route to the right LLM backend:
      ollama                       → _llm_stream_ollama  (native SDK, streaming)
      openai + Responses API model → _llm_stream_responses_api
      all other providers          → _llm_stream_openai  (streaming Chat Completions)
    """
    history.append({"role": "user", "content": user_text})

    if _use_responses_api():
        async for chunk in _llm_stream_responses_api(user_text):
            yield chunk
        return

    if current_provider == "ollama":
        async for chunk in _llm_stream_ollama(user_text):
            yield chunk
        return

    async for chunk in _llm_stream_openai(user_text):
        yield chunk


# ── TTS ───────────────────────────────────────────────────────────────────────

async def speak(text_gen):
    """Stream LLM tokens to ElevenLabs in real-time for minimal latency."""
    import time as _time
    loop = asyncio.get_event_loop()
    collected: list[str] = []
    tts_start = _time.monotonic()

    async def _eleven_streaming() -> bool:
        api_11 = _load_key("elevenlabs", "ELEVENLABS_API_KEY")
        if not api_11:
            return False
        uri = (f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input"
               f"?model_id={TTS_MODEL}&output_format=pcm_{SR}")
        try:
            async with ws_lib.connect(uri, open_timeout=6) as ws:
                await ws.send(json.dumps({
                    "text": " ",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                    "xi_api_key": api_11,
                    "generation_config": {"chunk_length_schedule": [50, 120, 200]},
                }))
                out = sd.OutputStream(samplerate=SR, channels=1, dtype="int16")
                out.start()
                got_audio = False

                async def _send():
                    async for chunk in text_gen:
                        collected.append(chunk)
                        if chunk.strip():
                            await ws.send(json.dumps({"text": chunk}))
                    await ws.send(json.dumps({"text": ""}))

                async def _recv():
                    nonlocal got_audio
                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                            if msg.get("audio"):
                                out.write(np.frombuffer(
                                    base64.b64decode(msg["audio"]), dtype=np.int16))
                                got_audio = True
                            if msg.get("isFinal"):
                                break
                        except Exception:
                            break

                try:
                    await asyncio.gather(_send(), _recv())
                finally:
                    out.stop(); out.close()
                return got_audio
        except asyncio.CancelledError:
            print("[tts] barge-in"); raise
        except Exception as e:
            print(f"[tts] ElevenLabs stream: {str(e)[:80]}")
            return False

    async def _pyttsx3_tts(text: str) -> bool:
        try:
            def _sapi():
                import pyttsx3
                eng = pyttsx3.init()
                voices = eng.getProperty("voices")
                if voices and tts_voice_idx < len(voices):
                    eng.setProperty("voice", voices[tts_voice_idx].id)
                eng.setProperty("rate", tts_rate)
                eng.setProperty("volume", 1.0)
                eng.say(text)
                eng.runAndWait()
            await loop.run_in_executor(None, _sapi)
            return True
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[tts] pyttsx3: {e}")
            return False

    async def _win32_tts(text: str) -> bool:
        """Speak using a Windows OneCore neural voice via win32com SAPI."""
        token_key = _onecore_voices.get(tts_voice_idx, "")
        if not token_key:
            print(f"[tts] win32: no token for voice index {tts_voice_idx}")
            return False
        try:
            def _speak_sync():
                import win32com.client  # pywin32
                tts_obj = win32com.client.Dispatch("SAPI.SpVoice")
                cat = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                cat.SetId(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices", False)
                tokens = cat.EnumerateTokens()
                for token in tokens:
                    try:
                        # token.Id = full registry path ending in the token key name
                        if token_key.lower() in token.Id.lower():
                            tts_obj.Voice = token
                            break
                    except Exception:
                        continue
                # Map WPM rate (175=normal) to SAPI rate scale (-10..+10)
                tts_obj.Rate   = max(-10, min(10, int((tts_rate - 175) / 20)))
                tts_obj.Volume = 100
                tts_obj.Speak(text, 0)  # 0 = SVSFDefault (synchronous)
            await loop.run_in_executor(None, _speak_sync)
            return True
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[tts] win32 onecore: {e}")
            return False

    async def _fallback_tts(text: str) -> bool:
        """Choose local TTS: OneCore win32 for index >= 100, else pyttsx3."""
        if tts_voice_idx >= 100:
            ok = await _win32_tts(text)
            if not ok:
                return await _pyttsx3_tts(text)
            return ok
        return await _pyttsx3_tts(text)

    try:
        await set_state("speaking")

        # Wrap text_gen: broadcast each token to UI as it arrives so the
        # console shows streaming text in real-time (not just after TTS finishes)
        stream_started = False
        async def _broadcasting_gen():
            nonlocal stream_started
            async for chunk in text_gen:
                collected.append(chunk)
                if chunk.strip():
                    if not stream_started:
                        await broadcast({"type": "stream_start"})
                        stream_started = True
                    await broadcast({"type": "token", "text": chunk})
                yield chunk

        if preferred_tts == "local":
            async for _ in _broadcasting_gen():
                pass
            if collected:
                await _fallback_tts("".join(collected))
        else:
            # Patch _eleven_streaming to use broadcasting gen
            _eleven_gen = _broadcasting_gen()
            async def _patched_eleven() -> bool:
                api_11 = _load_key("elevenlabs", "ELEVENLABS_API_KEY")
                if not api_11:
                    return False
                uri = (f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input"
                       f"?model_id={TTS_MODEL}&output_format=pcm_{SR}")
                try:
                    async with ws_lib.connect(uri, open_timeout=6) as ws:
                        await ws.send(json.dumps({
                            "text": " ",
                            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                            "xi_api_key": api_11,
                            "generation_config": {"chunk_length_schedule": [50, 120, 200]},
                        }))
                        out = sd.OutputStream(samplerate=SR, channels=1, dtype="int16")
                        out.start()
                        got_audio = False

                        async def _send():
                            async for chunk in _eleven_gen:
                                if chunk.strip():
                                    await ws.send(json.dumps({"text": chunk}))
                            await ws.send(json.dumps({"text": ""}))

                        async def _recv():
                            nonlocal got_audio
                            async for raw in ws:
                                try:
                                    msg = json.loads(raw)
                                    if msg.get("audio"):
                                        out.write(np.frombuffer(
                                            base64.b64decode(msg["audio"]), dtype=np.int16))
                                        got_audio = True
                                    if msg.get("isFinal"):
                                        break
                                except Exception:
                                    break

                        try:
                            await asyncio.gather(_send(), _recv())
                        finally:
                            out.stop(); out.close()
                        return got_audio
                except asyncio.CancelledError:
                    print("[tts] barge-in"); raise
                except Exception as e:
                    print(f"[tts] ElevenLabs stream: {str(e)[:80]}")
                    return False

            success = await _patched_eleven()
            if not success:
                if not collected:
                    async for _ in _broadcasting_gen():
                        pass
                if collected:
                    await _fallback_tts("".join(collected))
    except asyncio.CancelledError:
        return

    if collected:
        full_text = "".join(collected)
        # stream_finalize tells the UI to lock the streaming bubble into the chat
        await broadcast({"type": "stream_finalize", "text": full_text})
        await add_transcript("assistant", full_text)

    speak.last_duration = _time.monotonic() - tts_start

# ── Input handler ─────────────────────────────────────────────────────────────

async def handle_input(text: str) -> None:
    global speak_task, _input_busy
    _input_busy = True       # gate voice loop BEFORE any await
    try:
        # NOTE: don't call add_transcript("user") here — the UI already shows
        # the user message locally via addMessage() when the user hits Enter.
        # Voice input path calls add_transcript("user") directly in voice_loop.
        memory.add_task(text)
        await set_state("thinking")
        gen = llm_stream(text)
        speak_task = asyncio.create_task(speak(gen))
        await speak_task
        duration = getattr(speak, "last_duration", 0.0)
        await _drain(duration)
    finally:
        _input_busy = False  # always release even if an error occurs

async def _drain(tts_duration_secs: float = 0.0) -> None:
    global _tts_silence_until
    # Suppress VAD for the TTS audio duration + 3s room reverb tail (min 5s)
    silence_window = max(tts_duration_secs * 0.6 + 0.4, 1.0)  # min 1s (was 2s)
    _tts_silence_until = asyncio.get_event_loop().time() + silence_window
    await asyncio.sleep(0.4)
    if audio_q:
        while not audio_q.empty():
            try: audio_q.get_nowait()
            except asyncio.QueueEmpty: break
    await set_state("listening")

# ── Voice loop ────────────────────────────────────────────────────────────────

async def voice_loop() -> None:
    global audio_q, speak_task, _input_busy
    audio_q = asyncio.Queue()
    loop = asyncio.get_event_loop()
    barge = 0

    def cb(indata, _f, _t, _s):
        loop.call_soon_threadsafe(audio_q.put_nowait, indata.copy())

    vad = VAD()
    with sd.InputStream(samplerate=SR, channels=1, dtype="int16", blocksize=FRAME, callback=cb):
        await set_state("listening")
        winsound.Beep(880, 120)
        print(f"[operator] Ready — {current_provider}/{current_model}")
        while True:
            try:
                frame = await audio_q.get()
                rms   = float(np.sqrt(np.mean(frame.astype(np.float64)**2)))
                await broadcast_volume(rms / 2000.0)
                if muted: continue
                if _input_busy:          # text input is being processed — skip VAD entirely
                    continue
                if speak_task and not speak_task.done():
                    if rms > BARGE_RMS:
                        barge += 1
                        if barge >= BARGE_FRAMES:
                            speak_task.cancel(); barge = 0
                            _tts_silence_until = 0.0   # let VAD capture immediately after barge-in
                            await asyncio.sleep(0.15)
                    else:
                        barge = max(0, barge - 1)
                    continue
                else:
                    barge = 0
                # Post-TTS echo suppression: skip VAD during silence window
                if asyncio.get_event_loop().time() < _tts_silence_until:
                    continue
                ev, data = vad.feed(frame)
                if ev == "start":
                    winsound.Beep(400, 80); await set_state("recording")
                    await broadcast({"type": "partial_transcript", "text": "🎙 Listening…"})
                elif ev == "end":
                    winsound.Beep(700, 80); await set_state("thinking")
                    await broadcast({"type": "partial_transcript", "text": ""})
                    try:
                        text = await transcribe(data)
                    except Exception as e:
                        print(f"[stt] transcribe error: {e}")
                        await broadcast({"type": "state", "state": "listening"})
                        await broadcast({"type": "transcript", "role": "system", "text": f"[STT error: {e}]"})
                        vad.reset(); continue
                    if not text or len(text) < 3:
                        await set_state("listening"); vad.reset(); continue
                    print(f"[operator] 🎙 {text}")
                    await broadcast({"type": "partial_transcript", "text": f"🎙 {text}"})
                    await add_transcript("user", text)
                    memory.add_task(text)
                    gen = llm_stream(text)
                    await set_state("speaking")
                    _input_busy = True   # gate: don't let handle_input race with voice
                    try:
                        speak_task = asyncio.create_task(speak(gen))
                        await speak_task
                        duration = getattr(speak, "last_duration", 0.0)
                        await _drain(duration)
                    finally:
                        _input_busy = False
                    vad.reset()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[voice_loop] error: {e} — continuing")
                await asyncio.sleep(0.5)

# ── ElevenLabs Conversational Agent ──────────────────────────────────────────

def _make_tool_handler(tool_name: str):
    """Bridge: called from ElevenLabs SDK thread → exec_tool() in FastAPI event loop."""
    def handler(params: dict):
        if not _main_loop:
            return "Error: event loop not ready"
        try:
            future = asyncio.run_coroutine_threadsafe(exec_tool(tool_name, params), _main_loop)
            result = future.result(timeout=30)
            asyncio.run_coroutine_threadsafe(
                broadcast_action(tool_name, params, str(result)), _main_loop)
            return result
        except Exception as e:
            return f"Error in {tool_name}: {e}"
    return handler


_EL_TOOL_NAMES = [
    "read_screen", "screenshot", "click", "double_click", "right_click",
    "move_mouse", "drag", "scroll", "type_text", "press_key",
    "get_clipboard", "set_clipboard", "list_windows", "focus_window",
    "run_command", "read_file", "write_file", "list_files",
    "browser_open", "browser_click", "browser_fill", "browser_extract",
    "browser_screenshot", "browser_press",
]


async def _start_el_agent() -> None:
    global _el_conv, _el_thread, _el_active
    if _el_active:
        await broadcast({"type": "el_agent", "status": "already_running"}); return
    if not HAS_CONVAI:
        await broadcast({"type": "el_agent", "status": "error", "msg": "ConvAI SDK missing"}); return
    api_11 = _load_key("elevenlabs", "ELEVENLABS_API_KEY")
    if not api_11:
        await broadcast({"type": "el_agent", "status": "error", "msg": "No ElevenLabs API key"}); return

    client_tools = ClientTools()
    for name in _EL_TOOL_NAMES:
        client_tools.register(name, _make_tool_handler(name))

    el_client = ElevenLabs(api_key=api_11)
    _el_conv = Conversation(
        el_client,
        AGENT_ID,
        requires_auth=True,
        audio_interface=DefaultAudioInterface(),
        client_tools=client_tools,
        callback_agent_response=lambda text:
            asyncio.run_coroutine_threadsafe(add_transcript("assistant", text), _main_loop),
        callback_agent_response_correction=lambda orig, corr: None,
        callback_user_transcript=lambda text:
            asyncio.run_coroutine_threadsafe(add_transcript("user", text), _main_loop),
    )

    import threading
    def _run():
        global _el_active
        _el_active = True
        asyncio.run_coroutine_threadsafe(
            broadcast({"type": "el_agent", "status": "active"}), _main_loop)
        write_log("el_agent", "session started")
        try:
            _el_conv.start_session()
            conv_id = _el_conv.wait_for_session_end()
            write_log("el_agent", f"session ended: {conv_id}")
        except Exception as e:
            write_log("el_agent", f"error: {e}")
        finally:
            _el_active = False
            asyncio.run_coroutine_threadsafe(
                broadcast({"type": "el_agent", "status": "idle"}), _main_loop)

    _el_thread = threading.Thread(target=_run, daemon=True, name="el-agent")
    _el_thread.start()
    await broadcast({"type": "el_agent", "status": "starting"})
    write_log("el_agent", f"starting with {len(_EL_TOOL_NAMES)} tools")


async def _stop_el_agent() -> None:
    global _el_conv, _el_active
    if _el_conv and _el_active:
        try:
            _el_conv.end_session()
        except Exception:
            pass
    _el_active = False
    await broadcast({"type": "el_agent", "status": "idle"})
    write_log("el_agent", "stopped by user")

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    global _main_loop
    _main_loop = asyncio.get_event_loop()
    if not API_11:
        print("WARNING: ELEVENLABS_API_KEY not set — voice STT/TTS will use fallbacks")
    ollama_models = await fetch_ollama_models()
    PROVIDERS["ollama"]["models"] = ollama_models
    if ollama_models:
        global current_model
        current_model = ollama_models[0]
    write_log("startup", f"port={PORT} provider={current_provider} model={current_model}")

    async def _voice_supervisor():
        while True:
            try:
                await voice_loop()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[voice] crashed ({e}), restarting in 2s…")
                await broadcast({"type": "state", "state": "idle"})
                await asyncio.sleep(2)

    asyncio.create_task(_voice_supervisor())

    # Pre-warm Playwright so first browser_open call is instant
    try:
        asyncio.create_task(_prewarm_playwright())
    except Exception:
        pass

    await asyncio.sleep(1.2)


async def _prewarm_playwright():
    """Launch Playwright Chromium in background at startup to avoid cold-start delay."""
    try:
        await asyncio.sleep(3)          # let server fully initialise first
        await get_browser_page()
        print("[playwright] browser pre-warmed ✓")
    except Exception as e:
        print(f"[playwright] pre-warm skipped: {e}")
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    uvicorn.run("live_chat_app:app", host="0.0.0.0", port=PORT, log_level="warning")
