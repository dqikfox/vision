"""
VISION Voice Overlay  v3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Always-on-top floating widget.

Flow:
  Hold button → record mic
  Release     → Whisper transcribes
              → text pasted into whatever window was active
              → text sent to live_chat_app.py (port 8765) which has
                ALL tools: open chrome, run commands, create folders, etc.
              → AI reply streamed back and spoken via ElevenLabs

The backend (live_chat_app.py) is your VISION operator — it can do
anything: click, type, open apps, browse the web, manage files.
"""

import os, sys, time, threading, queue, re, json, ctypes
from pathlib import Path

import numpy as np
import sounddevice as sd
import win32gui, win32con
import tkinter as tk

# ── Load .env ──────────────────────────────────────────────
_env = Path(__file__).parent / ".env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip()

BACKEND_WS   = "ws://localhost:8765/ws"
BACKEND_HTTP = "http://localhost:8765"

# ── Colours ────────────────────────────────────────────────
BG      = "#080c18"
SURFACE = "#0d1625"
BLUE    = "#3b82f6"
GREEN   = "#22c55e"
CYAN    = "#06b6d4"
DIM     = "#334155"
RED     = "#ff4757"
TEXT    = "#cdd9e5"

# ── Audio ──────────────────────────────────────────────────
SAMPLE_RATE = 16000
BLOCK_SIZE  = 1024

# ── State ──────────────────────────────────────────────────
_recording      = False
_audio_frames   = []
_tts_queue      = queue.Queue()
_whisper_model  = None
_eleven_client  = None
_eleven_ok      = False
_lock           = threading.Lock()
_last_active_hwnd: int = 0   # unused — kept for future dictation mode


# ═══════════════════════════════════════════════════════════
# ElevenLabs / TTS
# ═══════════════════════════════════════════════════════════
def _setup_eleven():
    global _eleven_client, _eleven_ok
    key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("API_11")
    if not key:
        return False
    try:
        from elevenlabs import ElevenLabs
        _eleven_client = ElevenLabs(api_key=key)
        _eleven_ok = True
        return True
    except Exception:
        return False

def _tts_worker():
    while True:
        text = _tts_queue.get()
        if text is None:
            break
        text = text.strip()
        if not text:
            _tts_queue.task_done(); continue
        # Clean markdown
        text = re.sub(r"```[\s\S]*?```", "code block.", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"[*_~#>|]+", "", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        if len(text) > 1000:
            text = text[:1000] + "... and more."
        try:
            if _eleven_ok and _eleven_client:
                _speak_eleven(text)
            else:
                _speak_local(text)
        except Exception as e:
            print(f"[TTS ERR] {e}")
            try: _speak_local(text)
            except: pass
        _tts_queue.task_done()

def _mci_play(path: str):
    """Play an MP3/WAV via Windows MCI — no extra libraries needed."""
    import ctypes
    mci = ctypes.windll.winmm.mciSendStringW
    alias = "vision_tts"
    mci(f'open "{path}" type mpegvideo alias {alias}', None, 0, 0)
    mci(f"play {alias} wait", None, 0, 0)
    mci(f"close {alias}", None, 0, 0)

def _speak_eleven(text: str):
    import tempfile
    chunks = list(_eleven_client.text_to_speech.convert(
        voice_id=_eleven_voice_id(),
        text=text,
        model_id="eleven_turbo_v2_5",
        output_format="mp3_44100_128",
    ))
    audio = b"".join(chunks)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio)
        fname = f.name
    try:
        _mci_play(fname)
    finally:
        try: os.unlink(fname)
        except: pass

def _eleven_voice_id():
    try:
        vs = _eleven_client.voices.get_all().voices
        for v in vs:
            if v.name.lower() in ("rachel", "bella", "sarah"):
                return v.voice_id
        return vs[0].voice_id if vs else "21m00Tcm4TlvDq8ikWAM"
    except:
        return "21m00Tcm4TlvDq8ikWAM"

def _speak_local(text):
    """Fallback: PowerShell SAPI — no extra libraries, no hang."""
    import subprocess
    safe = text.replace('"', "'").replace('\n', ' ')
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        "$s.Rate=1;"
        f'$s.Speak("{safe}")'
    )
    subprocess.run(["powershell", "-NonInteractive", "-c", ps],
                   capture_output=True, timeout=30)

def speak(text: str):
    _tts_queue.put(text)

# ═══════════════════════════════════════════════════════════
# Whisper STT
# ═══════════════════════════════════════════════════════════
def _load_whisper():
    global _whisper_model
    if _whisper_model:
        return _whisper_model
    from faster_whisper import WhisperModel
    # Force CPU — avoids CUDA hang on device="auto"
    _whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _whisper_model

def _transcribe(audio: np.ndarray) -> str:
    result = [None]
    error  = [None]

    def _run():
        try:
            model = _load_whisper()
            f32 = audio.astype(np.float32) / 32768.0
            segs, _ = model.transcribe(f32, language="en", beam_size=3,
                                       vad_filter=True, vad_parameters={"min_silence_duration_ms": 500})
            result[0] = " ".join(s.text.strip() for s in segs).strip()
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=20)          # hard timeout — never hang UI forever
    if t.is_alive():
        return ""               # timed out
    if error[0]:
        print(f"[Whisper] {error[0]}")
        return ""
    return result[0] or ""

# ═══════════════════════════════════════════════════════════
# Backend WebSocket — sends text to live_chat_app.py
# which has ALL tools: click, run_command, open_browser, etc.
# ═══════════════════════════════════════════════════════════
_ws_response_queue: queue.Queue = queue.Queue()

def _send_to_backend(text: str, overlay) -> str:
    """Send transcription to live_chat_app.py and collect the AI reply."""
    try:
        import websocket as _ws   # websocket-client (sync)
        reply_chunks = []
        done = threading.Event()

        def on_message(ws, raw):
            try:
                msg = json.loads(raw)
                if msg.get("type") == "transcript" and msg.get("role") == "assistant":
                    reply_chunks.append(msg.get("text", ""))
                    # Don't set done here — keep collecting until state=listening
                elif msg.get("type") == "state" and msg.get("state") == "listening":
                    done.set()   # backend finished processing, all tokens received
            except Exception:
                pass

        def on_error(ws, err):
            print(f"[ws] {err}")
            done.set()

        def on_close(ws, *_):
            done.set()

        def on_open(ws):
            ws.send(json.dumps({"type": "input", "text": text}))

        ws_app = _ws.WebSocketApp(
            BACKEND_WS,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        t = threading.Thread(target=ws_app.run_forever, daemon=True)
        t.start()
        done.wait(timeout=60)   # allow up to 60s for tool execution
        ws_app.close()

        reply = " ".join(reply_chunks).strip()
        return reply
    except ImportError:
        return _send_to_backend_http(text)
    except Exception as e:
        print(f"[backend] {e}")
        return f"Backend error: {e}"

def _send_to_backend_http(text: str) -> str:
    """HTTP fallback — POST to /api/chat if WS fails."""
    try:
        import urllib.request
        data = json.dumps({"text": text}).encode()
        req = urllib.request.Request(
            f"{BACKEND_HTTP}/api/chat",
            data=data, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()).get("reply", "")
    except Exception as e:
        return f"HTTP error: {e}"

# ═══════════════════════════════════════════════════════════
# Direct AI chat — fallback if backend not running
# ═══════════════════════════════════════════════════════════
_chat_history: list[dict] = []
_openai_client = None

def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _openai_client

def _ask_ai_fallback(text: str) -> str:
    """Direct GPT call — only used when live_chat_app.py is not running."""
    _chat_history.append({"role": "user", "content": text})
    try:
        client = _get_openai()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content":
                    "You are VISION, a concise AI voice assistant. "
                    "Keep replies under 3 sentences. Plain spoken language only."},
                *_chat_history[-10:],
            ],
            max_tokens=300,
        )
        reply = response.choices[0].message.content.strip()
        _chat_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"AI error: {e}"

def _check_backend_alive() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(f"{BACKEND_HTTP}/api/health", timeout=2)
        return True
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════
# Audio
# ═══════════════════════════════════════════════════════════
def _audio_callback(indata, frames, t, s):
    if _recording:
        _audio_frames.append(indata.copy())

# ═══════════════════════════════════════════════════════════
# Floating Overlay UI
# ═══════════════════════════════════════════════════════════
class VoiceOverlay:
    VU_BARS = 16

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VISION Voice")
        self.root.overrideredirect(True)          # no title bar
        self.root.attributes("-topmost", True)    # always on top
        self.root.attributes("-alpha", 0.93)
        self.root.configure(bg=BG)

        # Position: bottom-right corner
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 220, 130
        self.root.geometry(f"{w}x{h}+{sw-w-18}+{sh-h-52}")

        self._build_ui()
        self._dragging = False
        self._drag_x = self._drag_y = 0

        # Pre-load whisper in background
        threading.Thread(target=_load_whisper, daemon=True).start()

        # TTS worker
        threading.Thread(target=_tts_worker, daemon=True).start()

        # VU meter update loop
        self._vu_job = None
        self._stream = None

    def _build_ui(self):
        r = self.root

        # Header bar (drag handle)
        hdr = tk.Frame(r, bg=SURFACE, height=22, cursor="fleur")
        hdr.pack(fill="x")
        hdr.bind("<Button-1>",   self._drag_start)
        hdr.bind("<B1-Motion>",  self._drag_motion)

        lbl = tk.Label(hdr, text="◈  VISION VOICE",
                       bg=SURFACE, fg=BLUE,
                       font=("Consolas", 8, "bold"),
                       anchor="w", padx=8)
        lbl.pack(side="left", fill="y")
        lbl.bind("<Button-1>",   self._drag_start)
        lbl.bind("<B1-Motion>",  self._drag_motion)

        close_btn = tk.Label(hdr, text="✕", bg=SURFACE, fg=DIM,
                             font=("Consolas", 9), padx=6, cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda _: self._quit())
        close_btn.bind("<Enter>",    lambda _: close_btn.config(fg=RED))
        close_btn.bind("<Leave>",    lambda _: close_btn.config(fg=DIM))

        # VU meter (canvas)
        self.vu_canvas = tk.Canvas(r, bg=BG, height=24,
                                   highlightthickness=0)
        self.vu_canvas.pack(fill="x", padx=8, pady=(6, 2))
        self._bars = []
        bar_w = 8; gap = 2
        total = self.VU_BARS * (bar_w + gap) - gap
        start_x = (220 - total) // 2
        for i in range(self.VU_BARS):
            x1 = start_x + i * (bar_w + gap)
            rect = self.vu_canvas.create_rectangle(
                x1, 6, x1 + bar_w, 20, fill=DIM, outline=""
            )
            self._bars.append(rect)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_lbl = tk.Label(r, textvariable=self.status_var,
                                   bg=BG, fg=DIM,
                                   font=("Consolas", 8))
        self.status_lbl.pack(pady=(0, 4))

        # Hold-to-talk button
        self.btn = tk.Button(
            r,
            text="🎙  HOLD TO TALK",
            bg=SURFACE, fg=TEXT,
            activebackground=BLUE, activeforeground="white",
            font=("Consolas", 9, "bold"),
            relief="flat", bd=0,
            padx=10, pady=6,
            cursor="hand2",
        )
        self.btn.pack(fill="x", padx=8, pady=(0, 8))
        self.btn.bind("<ButtonPress-1>",   self._on_press)
        self.btn.bind("<ButtonRelease-1>", self._on_release)

    # ── Drag ──────────────────────────────────────────────
    def _drag_start(self, ev):
        self._drag_x = ev.x_root - self.root.winfo_x()
        self._drag_y = ev.y_root - self.root.winfo_y()

    def _drag_motion(self, ev):
        x = ev.x_root - self._drag_x
        y = ev.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ── Status ─────────────────────────────────────────────
    def set_status(self, kind: str, msg: str):
        colours = {
            "ready":       DIM,
            "recording":   RED,
            "transcribing": CYAN,
            "injecting":   BLUE,
            "speaking":    GREEN,
            "error":       RED,
        }
        col = colours.get(kind, DIM)
        self.root.after(0, lambda: (
            self.status_var.set(msg),
            self.status_lbl.config(fg=col),
        ))

    # ── VU meter ───────────────────────────────────────────
    def _update_vu(self):
        if _audio_frames:
            data = _audio_frames[-1].flatten().astype(np.float32)
            rms  = float(np.sqrt(np.mean(data**2))) if data.size else 0
            db   = 20 * np.log10(rms / 32768 + 1e-9)
            lvl  = max(0, min(self.VU_BARS, int((db + 60) / 60 * self.VU_BARS)))
        else:
            lvl = 0
        for i, bar in enumerate(self._bars):
            if i < lvl:
                col = GREEN if i < self.VU_BARS * 0.6 else (
                      CYAN  if i < self.VU_BARS * 0.85 else RED)
            else:
                col = DIM
            self.vu_canvas.itemconfig(bar, fill=col)
        if _recording:
            self._vu_job = self.root.after(40, self._update_vu)
        else:
            # Fade bars to zero
            for bar in self._bars:
                self.vu_canvas.itemconfig(bar, fill=DIM)

    # ── Button press / release ─────────────────────────────
    def _on_press(self, _ev):
        global _recording, _audio_frames
        with _lock:
            if _recording:
                return
            _recording = True
            _audio_frames = []
        self.btn.config(bg=RED, fg="white", text="● RECORDING…")
        self.set_status("recording", "Recording…")
        self._update_vu()

    def _on_release(self, _ev):
        global _recording
        with _lock:
            if not _recording:
                return
            _recording = False
            frames = list(_audio_frames)

        self.btn.config(bg=SURFACE, fg=TEXT, text="🎙  HOLD TO TALK")

        def _process():
            if not frames:
                self.set_status("ready", "Ready")
                return
            audio = np.concatenate(frames).flatten()
            self.set_status("transcribing", "Transcribing…")
            text = _transcribe(audio)
            if not text:
                self.set_status("ready", "Nothing detected")
                return

            short = (text[:48] + "…") if len(text) > 50 else text
            self.set_status("injecting", f"You: {short}")

            # Send to backend (has all tools) or fallback to plain GPT — fully in background
            self.set_status("injecting", "Thinking…")
            if _check_backend_alive():
                reply = _send_to_backend(text, self)
            else:
                self.set_status("injecting", "Backend offline — using GPT")
                reply = _ask_ai_fallback(text)

            if reply:
                self.set_status("speaking", "Speaking…")
                speak(reply)
            self.set_status("ready", "Ready")

        threading.Thread(target=_process, daemon=True).start()

    # ── Quit ───────────────────────────────────────────────
    def _quit(self):
        _tts_queue.put(None)
        if self._stream:
            try: self._stream.stop(); self._stream.close()
            except: pass
        self.root.destroy()
        sys.exit(0)

    # ── Run ────────────────────────────────────────────────
    def run(self):
        _setup_eleven()
        label = "ElevenLabs" if _eleven_ok else "SAPI"

        backend_ok = _check_backend_alive()
        backend_label = "backend+tools" if backend_ok else "GPT-direct"
        self.set_status("ready", f"Ready  [{label} | {backend_label}]")

        greeting = (
            "Vision online. Backend connected — I can open apps, run commands, and control your computer."
            if backend_ok else
            "Vision ready. Say anything."
        )
        threading.Thread(target=speak, args=(greeting,), daemon=True).start()

        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1,
            dtype="int16", blocksize=BLOCK_SIZE,
            callback=_audio_callback,
        ):
            self.root.mainloop()


if __name__ == "__main__":
    VoiceOverlay().run()
