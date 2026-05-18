---
applyTo: "voice_overlay.py"
---

# Vision Voice Overlay (Tkinter GUI) Instructions

## Design Philosophy
The voice overlay is a **floating, draggable HUD** that displays Vision's real-time state. It should be:
- Minimalist and unobtrusive
- Always-on-top and semi-transparent
- Futuristic terminal aesthetic
- WCAG AA accessible
- Keyboard controllable

## Color Palette (Modern)
Use these constants (already defined at top of file):
```python
BG = "#0a0e1a"              # Deep background
SURFACE = "#131824"          # Panel background
SURFACE_LIGHT = "#1a2332"    # Lighter panels
BLUE_BRIGHT = "#60a5fa"      # Primary accent
GREEN_BRIGHT = "#34d399"     # Active/success
CYAN_BRIGHT = "#22d3ee"      # Thinking/processing
PURPLE_BRIGHT = "#a78bfa"    # Special states
RED_BRIGHT = "#f87171"       # Alerts/errors
ACCENT = "#f59e0b"           # Warnings/peaks
TEXT = "#e2e8f0"             # Primary text
TEXT_DIM = "#94a3b8"         # Secondary text
DIM = "#475569"              # Inactive elements
BORDER = "#1e293b"           # Subtle borders
```

## UI Component Guidelines

### Header
- Height: 28px minimum for easy dragging
- Add subtle border with `highlightbackground=BORDER`
- Use `BLUE_BRIGHT` for title to stand out
- Close button should have hover effect (red on mouseover)

### Labels
- Font: Consolas 8-9pt for readability
- Use `TEXT_DIM` for secondary info (STT, TTS)
- Use `CYAN_BRIGHT` for primary info (LLM model) - make it bold
- Add vertical spacing with `pady=2` between labels

### VU Meter (Canvas)
Use **gradient color zones** for better visual feedback:
- 0-50%: `GREEN` (normal levels)
- 50-73%: `GREEN_BRIGHT` (medium-high)
- 73-86%: `ACCENT` (orange warning)
- 86-100%: `RED_BRIGHT` (peak/clipping)

Canvas should have `SURFACE` background, not `BG`, for better contrast.

### Buttons
- Use flat relief: `relief="flat"`
- Remove borders: `borderwidth=0, highlightthickness=0`
- Add cursor change: `cursor="hand2"`
- Define active states: `activebackground`, `activeforeground`
- Use bright colors when active (e.g., `BLUE_BRIGHT` for Always-On enabled)

### Status Indicator
Use distinct colors for each state:
```python
STATE_COLORS = {
    "ready": TEXT_DIM,
    "listening": GREEN_BRIGHT,
    "recording": RED_BRIGHT,
    "thinking": CYAN_BRIGHT,
    "speaking": BLUE_BRIGHT,
    "error": RED_BRIGHT,
}
```

## WebSocket Communication
The overlay connects to Vision backend at `ws://localhost:8765/ws`.

### Message Handling Pattern
```python
def on_message(ws, raw):
    try:
        msg = json.loads(raw)
        msg_type = msg.get("type")

        if msg_type == "init":
            # Initial connection - update all info
            update_providers(msg)
        elif msg_type == "state":
            # State change - update status indicator
            overlay.set_status(msg["state"], msg["state"].capitalize())
        elif msg_type == "volume":
            # Audio level - update VU meter
            update_volume(msg["level"])
        # ... more handlers
    except Exception:
        logger.exception("Failed to parse message")
```

### Reconnection Logic
Always implement exponential backoff for reconnection:
```python
retry_delay = 1.0
while True:
    try:
        # Connect and run
        retry_delay = 1.0  # Reset on successful connection
    except Exception:
        logger.exception("Connection failed")
        time.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 30.0)  # Max 30 seconds
```

## Threading Best Practices
- WebSocket runs in background daemon thread
- **Never update Tkinter widgets from background thread**
- Use `root.after(0, callback)` to update UI from main thread

Example:
```python
def update_hud(self) -> None:
    # Safe: schedules update on main thread
    self.root.after(0, self._update_hud_now)

def _update_hud_now(self) -> None:
    # Runs on main thread - safe to update widgets
    self.llm_lbl.config(text=f"LLM: {_current_info['llm']}")
```

## Window Management
- Use `overrideredirect(True)` for frameless window
- Use `attributes("-topmost", True)` to stay on top
- Use `attributes("-alpha", 0.96)` for slight transparency
- Position in bottom-right corner by default:
```python
sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
w, h = 260, 190
self.root.geometry(f"{w}x{h}+{sw - w - 20}+{sh - h - 60}")
```

## Drag-and-Drop
Implement simple drag-and-drop for repositioning:
```python
def _drag_start(self, e: Any) -> None:
    self._drag_x = e.x_root - self.root.winfo_x()
    self._drag_y = e.y_root - self.root.winfo_y()

def _drag_motion(self, e: Any) -> None:
    x = e.x_root - self._drag_x
    y = e.y_root - self._drag_y
    self.root.geometry(f"+{x}+{y}")
```

Bind to header frame:
```python
hdr.bind("<Button-1>", self._drag_start)
hdr.bind("<B1-Motion>", self._drag_motion)
```

## Animation Loop
Use `root.after()` for smooth animations (50ms = 20fps):
```python
def _update_loop(self) -> None:
    # Update VU meter based on _current_volume
    update_vu_meter()

    # Schedule next frame
    self.root.after(50, self._update_loop)
```

## Accessibility
- Ensure all text is readable (minimum 8pt font)
- Use high contrast colors (WCAG AA: 4.5:1)
- Provide keyboard shortcuts (Ctrl+Alt+V to show/hide)
- Add tooltips for buttons (future enhancement)
- Support screen magnifiers (don't force small sizes)

## Error Handling
Show connection errors gracefully:
```python
def set_status(self, state: str, message: str) -> None:
    color = STATE_COLORS.get(state, TEXT_DIM)
    self.root.after(0, lambda: (
        self.status_var.set(message),
        self.status_lbl.config(fg=color)
    ))
```

## Performance
- Keep UI updates lightweight
- Batch multiple updates when possible
- Use canvas efficiently (pre-create rectangles, just update fill)
- Avoid creating new widgets in loops

## Testing
Test scenarios:
1. Launch without backend running (should show "Searching...")
2. Start backend while overlay is running (should auto-connect)
3. Stop backend while connected (should show "Disconnected" and retry)
4. Drag overlay to new position (should stay there)
5. Click mute button (should toggle state)
6. Click always-on button (should toggle continuous listening)
7. Close overlay (should exit cleanly)

## Type Hints
Always use modern type hints:
```python
from __future__ import annotations

def method(self, param: str) -> None:
    self.items: list[int] = []
    self.data: dict[str, Any] = {}
```

## Global State
Use module-level globals for WebSocket state (shared across threads):
```python
_ws_client: websocket.WebSocketApp | None = None
_ws_connected: bool = False
_is_muted: bool = False
_continuous_enabled: bool = False
_current_info: dict[str, str] = {...}
_current_state: str = "idle"
_current_volume: float = 0.0
```

Access with `global` keyword when modifying:
```python
def toggle_mute(self) -> None:
    global _is_muted
    _is_muted = not _is_muted
```
