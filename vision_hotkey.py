"""
VISION Hotkey Daemon
────────────────────
Runs silently in the background.
Ctrl+Alt+V  → launch / bring-to-front VISION Voice Overlay
Ctrl+Alt+Q  → quit this daemon

Run once at startup; it stays in the system tray area.
"""

import os, sys, subprocess, time, threading
import win32gui, win32con, win32process
import keyboard

OVERLAY_SCRIPT = r"C:\Users\msiul\.copilot\voice_overlay.py"
_overlay_pid = None
_lock = threading.Lock()


def _find_overlay_hwnd() -> int | None:
    """Return the HWND of the running overlay window, or None."""
    results = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "VISION Voice" in win32gui.GetWindowText(h):
            results.append(h)
    win32gui.EnumWindows(cb, None)
    return results[0] if results else None


def _overlay_running() -> bool:
    global _overlay_pid
    if _overlay_pid is None:
        return False
    try:
        # Check if process is still alive
        handle = win32process.OpenProcess(0x0400, False, _overlay_pid)  # PROCESS_QUERY_INFO
        if handle:
            import win32api
            code = win32api.GetExitCodeProcess(handle)
            return code == 259  # STILL_ACTIVE
    except Exception:
        pass
    return False


def launch_or_focus():
    global _overlay_pid
    with _lock:
        hwnd = _find_overlay_hwnd()
        if hwnd:
            # Already open — bring to front
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return

        if _overlay_running():
            return  # Running but window not found yet

        # Launch it
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable

        proc = subprocess.Popen(
            [pythonw, OVERLAY_SCRIPT],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        _overlay_pid = proc.pid
        print(f"[VISION] Launched overlay PID {_overlay_pid}")


def main():
    print("[VISION] Hotkey daemon active — Ctrl+Alt+V = overlay, Ctrl+Alt+Q = quit")

    keyboard.add_hotkey("ctrl+alt+v", launch_or_focus, suppress=True)
    keyboard.add_hotkey("ctrl+alt+q", lambda: sys.exit(0), suppress=True)

    # Keep alive
    keyboard.wait()


if __name__ == "__main__":
    main()
