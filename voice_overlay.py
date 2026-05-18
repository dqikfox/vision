"""
VISION Voice Overlay  v6 — Elite Remote HUD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Visual interface for the background VISION operator.
Displays: Active Models, STT/TTS Providers, VU Meter, Status.
Enhanced with modern gradients, shadows, and smooth animations.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
import tkinter as tk
from typing import Any

import websocket as ws_client

logger = logging.getLogger(__name__)

# ── Modern Color Palette ───────────────────────────────────
BG = "#0a0e1a"
SURFACE = "#131824"
SURFACE_LIGHT = "#1a2332"
BLUE = "#3b82f6"
BLUE_DARK = "#2563eb"
BLUE_BRIGHT = "#60a5fa"
GREEN = "#10b981"
GREEN_BRIGHT = "#34d399"
CYAN = "#06b6d4"
CYAN_BRIGHT = "#22d3ee"
PURPLE = "#8b5cf6"
PURPLE_BRIGHT = "#a78bfa"
DIM = "#475569"
DIM_LIGHT = "#64748b"
RED = "#ef4444"
RED_BRIGHT = "#f87171"
TEXT = "#e2e8f0"
TEXT_DIM = "#94a3b8"
ACCENT = "#f59e0b"
BORDER = "#1e293b"

BACKEND_WS = "ws://localhost:8765/ws"

# ── Global State ───────────────────────────────────────────
_ws_client = None
_ws_connected = False
_is_muted = False
_continuous_enabled = False
_current_info = {"stt": "Auto", "llm": "Connecting...", "tts": "Auto", "backend": "Offline"}
_current_state = "idle"
_current_volume = 0.0


def _ws_worker(overlay: VoiceOverlay) -> None:
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

            _ws_client = ws_client.WebSocketApp(
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

        # Header with modern styling and subtle border
        hdr = tk.Frame(r, bg=SURFACE, height=28, cursor="fleur", highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x")
        hdr.bind("<Button-1>", self._drag_start)
        hdr.bind("<B1-Motion>", self._drag_motion)

        title_lbl = tk.Label(
            hdr, text="◈ VISION HUD", bg=SURFACE, fg=BLUE_BRIGHT,
            font=("Consolas", 9, "bold"), padx=12
        )
        title_lbl.pack(side="left")

        close = tk.Label(
            hdr, text="✕", bg=SURFACE, fg=DIM_LIGHT,
            font=("Consolas", 10), padx=12, cursor="hand2"
        )
        close.pack(side="right")
        close.bind("<Button-1>", lambda _: self._quit())
        close.bind("<Enter>", lambda _: close.config(fg=RED_BRIGHT))
        close.bind("<Leave>", lambda _: close.config(fg=DIM_LIGHT))

        # HUD Indicators with improved styling
        self.hud = tk.Frame(r, bg=BG, padx=14, pady=10)
        self.hud.pack(fill="x")

        self.stt_lbl = tk.Label(
            self.hud, text="STT: Loading...", bg=BG, fg=TEXT_DIM,
            font=("Consolas", 8), anchor="w"
        )
        self.stt_lbl.pack(fill="x", pady=2)

        self.llm_lbl = tk.Label(
            self.hud, text="LLM: Disconnected", bg=BG, fg=CYAN_BRIGHT,
            font=("Consolas", 8, "bold"), anchor="w"
        )
        self.llm_lbl.pack(fill="x", pady=2)

        self.tts_lbl = tk.Label(
            self.hud, text="TTS: Loading...", bg=BG, fg=TEXT_DIM,
            font=("Consolas", 8), anchor="w"
        )
        self.tts_lbl.pack(fill="x", pady=2)

        # VU Canvas with modern bar styling
        self.vu = tk.Canvas(r, bg=SURFACE, height=28, highlightthickness=0)
        self.vu.pack(fill="x", padx=14, pady=6)
        self._bars: list[int] = []
        bar_width = 9
        bar_spacing = 2
        for i in range(self.VU_BARS):
            x1 = i * (bar_width + bar_spacing) + 4
            x2 = x1 + bar_width
            b = self.vu.create_rectangle(
                x1, 6, x2, 22, fill=DIM, outline="", width=0
            )
            self._bars.append(b)

        # Status with improved visibility
        self.status_var = tk.StringVar(value="Searching for backend...")
        self.status_lbl = tk.Label(
            r, textvariable=self.status_var, bg=BG, fg=TEXT_DIM,
            font=("Consolas", 8)
        )
        self.status_lbl.pack(pady=4)

        # Controls with modern button styling
        ctrls = tk.Frame(r, bg=BG, pady=10)
        ctrls.pack(fill="x", padx=14)

        self.mute_btn = tk.Button(
            ctrls,
            text="🎙 UNMUTE",
            bg=RED,
            fg="white",
            font=("Consolas", 8, "bold"),
            relief="flat",
            activebackground=RED_BRIGHT,
            activeforeground="white",
            cursor="hand2",
            borderwidth=0,
            highlightthickness=0,
            command=self.toggle_mute,
        )
        self.mute_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.cont_btn = tk.Button(
            ctrls,
            text="∞ ALWAYS-ON",
            bg=SURFACE_LIGHT,
            fg=TEXT_DIM,
            font=("Consolas", 8, "bold"),
            relief="flat",
            activebackground=BLUE,
            activeforeground="white",
            cursor="hand2",
            borderwidth=0,
            highlightthickness=0,
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
                bg=BLUE_BRIGHT if enabled else SURFACE_LIGHT,
                fg="white" if enabled else TEXT_DIM,
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
            # Gradient color based on level position
            if i < lvl:
                if i >= self.VU_BARS - 3:  # Peak zone
                    col = RED_BRIGHT
                elif i >= self.VU_BARS - 6:  # High zone
                    col = ACCENT
                elif i >= self.VU_BARS // 2:  # Medium-high zone
                    col = GREEN_BRIGHT
                else:  # Low zone
                    col = GREEN
            else:
                col = DIM
            self.vu.itemconfig(b, fill=col)

        self.root.after(50, self._update_loop)

    def _drag_start(self, e: Any) -> None:
        self._drag_x, self._drag_y = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()

    def _drag_motion(self, e: Any) -> None:
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    def set_status(self, k: str, m: str) -> None:
        c = {
            "ready": TEXT_DIM,
            "listening": GREEN_BRIGHT,
            "recording": RED_BRIGHT,
            "thinking": CYAN_BRIGHT,
            "speaking": BLUE_BRIGHT,
            "error": RED_BRIGHT,
        }
        self.root.after(0, lambda: (self.status_var.set(m), self.status_lbl.config(fg=c.get(k, TEXT_DIM))))

    def _quit(self) -> None:
        self.root.destroy()
        sys.exit(0)

    def run(self) -> None:
        self._update_loop()
        self.root.mainloop()


if __name__ == "__main__":
    VoiceOverlay().run()
