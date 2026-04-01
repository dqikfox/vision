"""
VISION Voice CLI Bridge  v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Push-to-talk STT (faster-whisper) + TTS (ElevenLabs/pyttsx3)
Runs inside VS Code terminal.  Transcripts inject directly into
the last-focused VS Code input (Copilot Chat, terminal, editor).

Hotkeys  (global — work even when terminal is not focused):
  RIGHT CTRL    Hold to record, release to transcribe + inject
  F2            Read clipboard aloud via TTS
  F3            Toggle auto-TTS (speaks every new clipboard change)
  F6            Re-inject last transcript into VS Code
  ESC           Quit
"""

import sys, os, time, threading, queue, re
from pathlib import Path

import numpy as np
import sounddevice as sd
import pyperclip
import keyboard
import pyttsx3
import win32gui, win32con, win32api, win32process

# ── Load .env ──────────────────────────────────────
_env = Path(__file__).parent / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# ── ANSI colours ───────────────────────────────────
ESC = "\033["
R  = f"{ESC}0m";   B  = f"{ESC}38;2;59;130;246m"
C  = f"{ESC}38;2;6;182;212m";  G  = f"{ESC}38;2;34;197;94m"
Y  = f"{ESC}38;2;251;191;36m"; D  = f"{ESC}38;2;71;85;105m"
RD = f"{ESC}38;2;255;71;87m";  BLD = f"{ESC}1m"
W  = 64

def _ts():
    return time.strftime("%H:%M:%S")

def status(label: str, msg: str, col=C):
    sys.stdout.write(f"\r  {D}[{_ts()}]{R} {col}{BLD}{label:12}{R} {msg}\n")
    sys.stdout.flush()

def banner():
    os.system("cls" if os.name == "nt" else "clear")
    tts_label = f"{G}ElevenLabs{R}" if _eleven_ok else f"{Y}pyttsx3{R}"
    lines = [
        f"  +{'='*W}+",
        f"  |  {BLD}{B}VISION Voice CLI  v2{R}{'':>43}|",
        f"  |  {D}{'─'*W}{R}  |",
        f"  |  {Y}RIGHT CTRL{R}  {D}Hold → record, release → transcribe + inject{R}   |",
        f"  |  {Y}F2        {R}  {D}Read clipboard aloud (Copilot reply → TTS){R}     |",
        f"  |  {Y}F3        {R}  {D}Toggle auto-TTS mode{R}                           |",
        f"  |  {Y}F6        {R}  {D}Re-inject last transcript into VS Code{R}         |",
        f"  |  {Y}ESC       {R}  {D}Quit{R}                                           |",
        f"  |  {D}{'─'*W}{R}  |",
        f"  |  TTS: {tts_label}    STT: {G}faster-whisper base.en{R}          |",
        f"  +{'='*W}+",
    ]
    for l in lines:
        print(l)
    print()

# ── Audio config ───────────────────────────────────
SAMPLE_RATE = 16000
BLOCK_SIZE  = 1024

# ── Global state ───────────────────────────────────
_recording       = False
_audio_frames: list[np.ndarray] = []
_tts_queue: queue.Queue = queue.Queue()
_auto_tts        = False
_whisper_model   = None
_eleven_client   = None
_eleven_ok       = False
_last_transcript = ""
_lock            = threading.Lock()

# ── ElevenLabs ─────────────────────────────────────
def _setup_eleven() -> bool:
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

_pyttsx_engine = None
def _get_pyttsx():
    global _pyttsx_engine
    if _pyttsx_engine is None:
        _pyttsx_engine = pyttsx3.init()
        _pyttsx_engine.setProperty("rate", 175)
        _pyttsx_engine.setProperty("volume", 0.9)
    return _pyttsx_engine

def _tts_worker():
    while True:
        text = _tts_queue.get()
        if text is None:
            break
        text = text.strip()
        if not text:
            _tts_queue.task_done(); continue
        # Clean markdown for speech
        text = re.sub(r"```[\s\S]*?```", "code block.", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"[*_~#>]+", "", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        if len(text) > 900:
            text = text[:900] + "... and more."
        try:
            if _eleven_ok and _eleven_client:
                _speak_eleven(text)
            else:
                _speak_local(text)
        except Exception as e:
            status("TTS ERR", str(e)[:80], RD)
        _tts_queue.task_done()

def _speak_eleven(text: str):
    import subprocess, tempfile
    chunks = list(_eleven_client.text_to_speech.convert(
        voice_id=_eleven_voice_id(),
        text=text,
        model_id="eleven_turbo_v2_5",
    ))
    audio = b"".join(chunks)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio); fname = f.name
    # Use Windows Media Player via PowerShell
    ps = (
        "Add-Type -AssemblyName presentationCore;"
        f"$p=[System.Windows.Media.MediaPlayer]::new();"
        f"$p.Open([uri]'{fname}'); $p.Play();"
        "Start-Sleep -Milliseconds 500;"
        "while($p.Position -lt $p.NaturalDuration.TimeSpan){{Start-Sleep -Milliseconds 200}};"
        "$p.Close()"
    )
    subprocess.run(["powershell", "-c", ps], capture_output=True)
    try: os.unlink(fname)
    except: pass

def _eleven_voice_id() -> str:
    try:
        vs = _eleven_client.voices.get_all().voices
        for v in vs:
            if v.name.lower() in ("rachel", "bella", "antoni"):
                return v.voice_id
        return vs[0].voice_id if vs else "21m00Tcm4TlvDq8ikWAM"
    except:
        return "21m00Tcm4TlvDq8ikWAM"

def _speak_local(text: str):
    _get_pyttsx().say(text); _get_pyttsx().runAndWait()

def speak(text: str):
    _tts_queue.put(text)

# ── Whisper ────────────────────────────────────────
def _load_whisper():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    status("WHISPER", f"Loading model… {D}(first run only){R}", Y)
    from faster_whisper import WhisperModel
    _whisper_model = WhisperModel("base.en", device="auto", compute_type="int8")
    status("WHISPER", f"{G}Ready{R}", G)
    return _whisper_model

def _transcribe(audio: np.ndarray) -> str:
    model = _load_whisper()
    f32 = audio.astype(np.float32) / 32768.0
    segs, _ = model.transcribe(f32, language="en", beam_size=5, vad_filter=True)
    return " ".join(s.text.strip() for s in segs).strip()

# ── VS Code window injection ───────────────────────
def _find_vscode_hwnd() -> int | None:
    """Return the hwnd of the frontmost Visual Studio Code window."""
    results = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Visual Studio Code" in title:
                results.append(hwnd)
    win32gui.EnumWindows(cb, None)
    return results[0] if results else None

def _inject_into_vscode(text: str):
    """
    Bring VS Code to the foreground, restoring last focus (Copilot Chat
    input or terminal), then paste the transcript.
    """
    hwnd = _find_vscode_hwnd()
    if not hwnd:
        status("INJECT", f"{RD}VS Code window not found{R}", RD)
        return
    # Restore VS Code to foreground — Windows restores last focused control
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.25)   # let it paint
    # Paste via Ctrl+V
    pyperclip.copy(text)
    keyboard.send("ctrl+v")
    status("INJECT", f"{G}Pasted into VS Code{R}", G)

# ── Visualiser (inline, in-place) ─────────────────
def _draw_vu(frames: list[np.ndarray], stop_ev: threading.Event):
    bars = 24
    while not stop_ev.is_set():
        if frames:
            a = frames[-1].flatten().astype(np.float32)
            rms = float(np.sqrt(np.mean(a**2))) if a.size else 0
            db  = 20 * np.log10(rms / 32768 + 1e-9)
            lvl = max(0, min(bars, int((db + 60) / 60 * bars)))
            bar = f"{G}{'█'*lvl}{D}{'░'*(bars-lvl)}{R}"
            pct = int(lvl / bars * 100)
            sys.stdout.write(f"\r  {RD}{BLD}◉ REC{R}  {bar}  {Y}{pct:3d}%{R}   ")
            sys.stdout.flush()
        time.sleep(0.04)
    sys.stdout.write(f"\r{' ' * 60}\r")
    sys.stdout.flush()

# ── Recording ──────────────────────────────────────
def _audio_callback(indata, frames, t, s):
    if _recording:
        _audio_frames.append(indata.copy())

def _start_rec():
    global _recording, _audio_frames
    with _lock:
        if _recording: return
        _recording = True
        _audio_frames = []

def _stop_and_process():
    global _recording, _last_transcript
    with _lock:
        if not _recording: return
        _recording = False
        frames = list(_audio_frames)
    if not frames:
        status("LISTEN", f"{D}No audio{R}", D); return
    stop_ev = threading.Event()
    audio = np.concatenate(frames).flatten()
    status("WHISPER", "Transcribing…", C)
    text = _transcribe(audio)
    if not text:
        status("WHISPER", f"{D}[silence or unclear]{R}", D); return
    _last_transcript = text
    pyperclip.copy(text)
    print(f"\n  {B}{BLD}YOU:{R} {BLD}{text}{R}\n")
    _inject_into_vscode(text)

# ── Hotkeys ────────────────────────────────────────
def _on_rctrl(ev):
    if ev.event_type == keyboard.KEY_DOWN and not _recording:
        _start_rec()
        # Start VU in background
        threading.Thread(
            target=_draw_vu,
            args=(_audio_frames, _stop_event := threading.Event()),
            daemon=True
        ).start()
    elif ev.event_type == keyboard.KEY_UP and _recording:
        threading.Thread(target=_stop_and_process, daemon=True).start()

def _on_f2():
    text = pyperclip.paste().strip()
    if text:
        status("TTS", f"Speaking {len(text)} chars…", C)
        speak(text)
    else:
        status("TTS", f"{D}Clipboard empty{R}", D)

def _on_f3():
    global _auto_tts
    _auto_tts = not _auto_tts
    lbl = f"{G}ON{R}" if _auto_tts else f"{RD}OFF{R}"
    status("AUTO-TTS", f"Auto-read {lbl}", C)

def _on_f6():
    if _last_transcript:
        _inject_into_vscode(_last_transcript)
    else:
        status("INJECT", f"{D}No transcript yet{R}", D)

# ── Clipboard watcher ──────────────────────────────
def _clip_watcher():
    last = ""
    while True:
        time.sleep(0.6)
        if _auto_tts and not _recording:
            try:
                cur = pyperclip.paste()
                if cur != last and len(cur) > 15:
                    last = cur
                    speak(cur)
            except: pass

# ── Main ───────────────────────────────────────────
def main():
    global _eleven_ok
    _eleven_ok = _setup_eleven()
    banner()

    threading.Thread(target=_load_whisper, daemon=True).start()
    threading.Thread(target=_tts_worker, daemon=True).start()
    threading.Thread(target=_clip_watcher, daemon=True).start()

    keyboard.hook_key("right ctrl", _on_rctrl, suppress=True)
    keyboard.add_hotkey("f2", _on_f2, suppress=False)
    keyboard.add_hotkey("f3", _on_f3, suppress=False)
    keyboard.add_hotkey("f6", _on_f6, suppress=False)

    status("READY", f"{G}Hold RIGHT CTRL to speak → auto-injects into VS Code Copilot Chat{R}", G)
    if _eleven_ok:
        speak("Vision Voice CLI ready. Hold right control to speak.")

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1,
            dtype="int16", blocksize=BLOCK_SIZE,
            callback=_audio_callback,
        ):
            keyboard.wait("esc")
    except KeyboardInterrupt:
        pass
    status("BYE", "Shutting down.", D)
    _tts_queue.put(None)

if __name__ == "__main__":
    main()