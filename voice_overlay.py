"""
VISION Voice Overlay  v5 — Elite Remote HUD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Visual interface for the background VISION operator.
Displays: Active Models, STT/TTS Providers, VU Meter, Status.
"""

import json
import logging
import sys
import threading
import time
import tkinter as tk
from typing import Any

import websocket

logger = logging.getLogger(__name__)

# ── Colours ────────────────────────────────────────────────
BG = "#080c18"
SURFACE = "#0d1625"
BLUE = "#3b82f6"
GREEN = "#22c55e"
CYAN = "#06b6d4"
DIM = "#334155"
RED = "#ff4757"
TEXT = "#cdd9e5"

BACKEND_WS = "ws://localhost:8765/ws"

# ── Global State ───────────────────────────────────────────
_ws_client = None
_ws_connected = False
_is_muted = False
_continuous_enabled = False
_current_info = {"stt": "Auto", "llm": "Connecting...", "tts": "Auto", "backend": "Offline"}
_current_state = "idle"
_current_volume = 0.0


def _ws_worker(overlay: "VoiceOverlay") -> None:
    global _ws_client, _ws_connected, _is_muted, _continuous_enabled
    global _current_info, _current_state, _current_volume
    retry_delay = 1.0
    while True:
        try:

            def on_message(ws, raw):
                try:
                    msg = json.loads(raw)
                    t = msg.get("type")
                    if t == "init":
                        _current_info["llm"] = f"{msg.get('provider', '')} / {msg.get('model', '')}"
                        _current_info["stt"] = msg.get("voice", {}).get("preferred_stt", "auto")
                        _current_info["tts"] = msg.get("voice", {}).get("preferred_tts", "auto")
                        _continuous_enabled = msg.get("continuous_listening", False)
                        _is_muted = msg.get("muted", False)
                        overlay.update_hud()
                        overlay.set_continuous_btn(_continuous_enabled)
                        overlay.set_mute_btn(_is_muted)
                    elif t == "model_changed":
                        _current_info["llm"] = f"{msg.get('provider', '')} / {msg.get('model', '')}"
                        overlay.update_hud()
                    elif t == "voice_settings":
                        _current_info["stt"] = msg.get("preferred_stt", _current_info["stt"])
                        _current_info["tts"] = msg.get("preferred_tts", _current_info["tts"])
                        overlay.update_hud()
                    elif t == "stt_active":
                        provider = msg.get("provider")
                        if provider:
                            _current_info["stt"] = provider
                            overlay.update_hud()
                    elif t == "tts_active":
                        provider = msg.get("provider")
                        if provider:
                            _current_info["tts"] = provider
                            overlay.update_hud()
                    elif t == "state":
                        _current_state = msg.get("state", "idle")
                        overlay.set_status(_current_state, _current_state.capitalize())
                    elif t == "volume":
                        _current_volume = float(msg.get("level", 0.0))
                    elif t == "continuous_state":
                        _continuous_enabled = msg.get("enabled", False)
                        overlay.set_continuous_btn(_continuous_enabled)
                    elif t == "mute_state":
                        _is_muted = msg.get("muted", False)
                        overlay.set_mute_btn(_is_muted)
                except Exception:
                    logger.exception("Failed to parse websocket message")

            def on_error(ws, err):
                overlay.set_status("error", f"Socket error: {err}")

            def on_close(ws, *_):
                global _ws_connected
                _ws_connected = False
                _current_info["backend"] = "Offline"
                overlay.update_hud()
                overlay.set_status("error", "Disconnected")

            def on_open(ws):
                global _ws_connected
                _ws_connected = True
                _current_info["backend"] = "Connected"
                overlay.update_hud()
                overlay.set_status("ready", "Connected")
                # Request initial state
                ws.send(json.dumps({"type": "get_state"}))

            _ws_client = websocket.WebSocketApp(
                BACKEND_WS, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close
            )
            _ws_client.run_forever()
            retry_delay = 1.0
        except Exception:
            logger.exception("WebSocket worker failed")

        time.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 30.0)


# ═══════════════════════════════════════════════════════════
# Floating Overlay UI
# ════════════════════════════════━━━━━━━━━━━━━━━━━━━━━━━━━━
class VoiceOverlay:
    VU_BARS = 22

    def __init__(self) -> None:
        self.root: tk.Tk = tk.Tk()
        self.root.title("VISION HUD")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.configure(bg=BG)

        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = 260, 190
        self.root.geometry(f"{w}x{h}+{sw - w - 20}+{sh - h - 60}")

        self._build_ui()
        self._dragging: bool = False
        self._drag_x: int = 0
        self._drag_y: int = 0

        threading.Thread(target=_ws_worker, args=(self,), daemon=True).start()

    def _build_ui(self) -> None:
        r = self.root
        hdr = tk.Frame(r, bg=SURFACE, height=26, cursor="fleur")
        hdr.pack(fill="x")
        hdr.bind("<Button-1>", self._drag_start)
        hdr.bind("<B1-Motion>", self._drag_motion)

        tk.Label(hdr, text="◈ VISION HUD", bg=SURFACE, fg=BLUE, font=("Consolas", 8, "bold"), padx=10).pack(side="left")

        close = tk.Label(hdr, text="✕", bg=SURFACE, fg=DIM, font=("Consolas", 9), padx=10, cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", lambda _: self._quit())

        # HUD Indicators
        self.hud = tk.Frame(r, bg=BG, padx=12, pady=8)
        self.hud.pack(fill="x")

        self.stt_lbl = tk.Label(self.hud, text="STT: Loading...", bg=BG, fg=DIM, font=("Consolas", 7), anchor="w")
        self.stt_lbl.pack(fill="x")
        self.llm_lbl = tk.Label(self.hud, text="LLM: Disconnected", bg=BG, fg=CYAN, font=("Consolas", 7), anchor="w")
        self.llm_lbl.pack(fill="x")
        self.tts_lbl = tk.Label(self.hud, text="TTS: Loading...", bg=BG, fg=DIM, font=("Consolas", 7), anchor="w")
        self.tts_lbl.pack(fill="x")

        # VU Canvas
        self.vu = tk.Canvas(r, bg=BG, height=24, highlightthickness=0)
        self.vu.pack(fill="x", padx=12, pady=2)
        self._bars: list[int] = []
        for i in range(self.VU_BARS):
            b = self.vu.create_rectangle(i * 11 + 2, 5, i * 11 + 10, 19, fill=DIM, outline="")
            self._bars.append(b)

        # Status
        self.status_var = tk.StringVar(value="Searching for backend...")
        self.status_lbl = tk.Label(r, textvariable=self.status_var, bg=BG, fg=DIM, font=("Consolas", 8))
        self.status_lbl.pack(pady=2)

        # Controls
        ctrls = tk.Frame(r, bg=BG, pady=8)
        ctrls.pack(fill="x", padx=12)

        self.mute_btn = tk.Button(
            ctrls,
            text="🎙 UNMUTE",
            bg=RED,
            fg="white",
            font=("Consolas", 8, "bold"),
            relief="flat",
            command=self.toggle_mute,
        )
        self.mute_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.cont_btn = tk.Button(
            ctrls,
            text="∞ ALWAYS-ON",
            bg=SURFACE,
            fg=DIM,
            font=("Consolas", 8, "bold"),
            relief="flat",
            command=self.toggle_always_on,
        )
        self.cont_btn.pack(side="right", expand=True, fill="x")

    def update_hud(self) -> None:
        self.root.after(0, self._update_hud_now)

    def _update_hud_now(self) -> None:
        self.stt_lbl.config(text=f"STT: {_current_info['stt']}")
        self.llm_lbl.config(text=f"LLM: {_current_info['llm']}")
        self.tts_lbl.config(text=f"TTS: {_current_info['tts']}")

    def set_continuous_btn(self, enabled: bool) -> None:
        self.root.after(
            0,
            lambda: self.cont_btn.config(
                bg=BLUE if enabled else SURFACE,
                fg="white" if enabled else DIM,
            ),
        )

    def set_mute_btn(self, muted: bool) -> None:
        self.root.after(
            0,
            lambda: self.mute_btn.config(
                text="🎙 UNMUTE" if muted else "🎙 MUTE",
                bg=RED if muted else SURFACE,
                fg="white" if muted else TEXT,
            ),
        )

    def toggle_mute(self) -> None:
        global _is_muted
        if not _ws_connected:
            return
        _is_muted = not _is_muted
        _ws_client.send(json.dumps({"type": "set_mute", "muted": _is_muted}))
        self.set_mute_btn(_is_muted)

    def toggle_always_on(self) -> None:
        global _continuous_enabled
        if not _ws_connected:
            return
        _continuous_enabled = not _continuous_enabled
        _ws_client.send(json.dumps({"type": "set_continuous", "enabled": _continuous_enabled}))
        self.set_continuous_btn(_continuous_enabled)

    def _update_loop(self) -> None:
        lvl = min(self.VU_BARS, int(_current_volume * self.VU_BARS))
        for i, b in enumerate(self._bars):
            col = GREEN if i < lvl else DIM
            if i >= self.VU_BARS - 2 and lvl > self.VU_BARS - 2:
                col = RED  # Peak
            self.vu.itemconfig(b, fill=col)

        self.root.after(50, self._update_loop)

    def _drag_start(self, e: Any) -> None:
        self._drag_x, self._drag_y = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()

    def _drag_motion(self, e: Any) -> None:
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    def set_status(self, k: str, m: str) -> None:
        c = {"ready": DIM, "listening": GREEN, "recording": RED, "thinking": CYAN, "speaking": BLUE, "error": RED}
        self.root.after(0, lambda: (self.status_var.set(m), self.status_lbl.config(fg=c.get(k, DIM))))

    def _quit(self) -> None:
        self.root.destroy()
        sys.exit(0)

    def run(self) -> None:
        self._update_loop()
        self.root.mainloop()


if __name__ == "__main__":
    VoiceOverlay().run()
