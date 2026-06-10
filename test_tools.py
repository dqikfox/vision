"""Quick tool interaction test for Vision operator."""
import asyncio
import json

import websockets

URI = "ws://localhost:8765/ws"


def safe_print(text: str) -> None:
    """Print text safely on Windows consoles that still use cp1252."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


async def recv_until(ws, types, timeout=60):
    """Collect messages until one of the given types appears."""
    results = []
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(raw)
            t = msg.get("type", "")
            results.append(msg)
            if t in types:
                return results
        except TimeoutError:
            continue
    return results


async def drain_ws(ws, quiet_timeout=0.2, max_wait=1.0):
    """Discard leftover websocket messages without hanging on continuous volume updates."""
    deadline = asyncio.get_running_loop().time() + max_wait
    while asyncio.get_running_loop().time() < deadline:
        try:
            await asyncio.wait_for(ws.recv(), timeout=quiet_timeout)
        except TimeoutError:
            return


async def recv_action(ws, expected_action, timeout=30):
    """Wait for a specific action event, ignoring unrelated messages."""
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(raw)
        except TimeoutError:
            continue
        if msg.get("type") == "action" and msg.get("action") == expected_action:
            return msg
    return None


async def prepare_session(ws, mode=None):
    """Disable voice-loop interference so tool tests exercise deterministic websocket flows."""
    await ws.send(json.dumps({"type": "set_continuous", "enabled": False}))
    await ws.send(json.dumps({"type": "set_mute", "muted": True}))
    if mode is not None:
        await ws.send(json.dumps({"type": "set_mode", "mode": mode}))
    await asyncio.sleep(0.5)
    await drain_ws(ws, max_wait=1.5)


async def main():
    async with websockets.connect(URI) as ws:
        # Init
        init = json.loads(await asyncio.wait_for(ws.recv(), 10))
        safe_print(f"[INIT] provider={init.get('provider')} model={init.get('model')}")
        await prepare_session(ws)

        # ── Test 1: Direct screenshot ──────────────────────────────────────────
        print("\n[TEST 1] Direct screenshot tool")
        await drain_ws(ws)
        await ws.send(
            json.dumps({"type": "execute_tool", "tool": "screenshot", "args": {}})
        )
        msgs = await recv_until(ws, {"screenshot", "action"}, timeout=20)
        screenshot_ok = False
        for m in msgs:
            if m.get("type") == "screenshot":
                screenshot_ok = True
                safe_print(f"  PASS - screenshot received ({len(m['data'])} b64 chars)")
            elif m.get("type") == "action" and m.get("action") == "screenshot":
                screenshot_ok = True
                safe_print(f"  action: {m['action']} -> {str(m['result'])[:80]}")
        if not screenshot_ok:
            safe_print("  FAIL - no screenshot event received")
        await drain_ws(ws)

        # ── Test 2: run_command ────────────────────────────────────────────────
        print("\n[TEST 2] run_command tool")
        await ws.send(
            json.dumps(
                {
                    "type": "execute_tool",
                    "tool": "run_command",
                    "args": {"command": "echo vision-tool-test"},
                }
            )
        )
        run_command_action = await recv_action(ws, "run_command", timeout=20)
        if run_command_action:
            safe_print(f"  PASS - result: {run_command_action['result'].strip()}")
        else:
            safe_print("  FAIL - no run_command action received")

        # ── Test 3: NL → tool call (screenshot) ───────────────────────────────
        safe_print("\n[TEST 3] Natural language -> screenshot tool call")
        safe_print("  Sending: 'take a screenshot and tell me what you see'")
        await prepare_session(ws, mode="operator")
        await ws.send(
            json.dumps(
                {
                    "type": "input",
                    "text": "take a screenshot and tell me what you see",
                }
            )
        )
        got_tool = False
        got_reply = False
        deadline = asyncio.get_running_loop().time() + 120
        while asyncio.get_running_loop().time() < deadline and not (got_tool and got_reply):
            try:
                raw = await asyncio.wait_for(ws.recv(), 8)
                m = json.loads(raw)
                t = m.get("type", "")
                if t == "state":
                    safe_print(f"  state -> {m['state']}")
                elif t == "action" and m.get("action") in {"screenshot", "read_screen"}:
                    got_tool = True
                    safe_print(f"  TOOL CALLED: {m['action']} -> {str(m['result'])[:80]}")
                elif t == "screenshot":
                    got_tool = True
                    safe_print(f"  SCREENSHOT sent to UI ({len(m['data'])} b64 chars)")
                elif t == "transcript" and m.get("role") == "assistant":
                    got_reply = True
                    safe_print(f"  AI REPLY: {m['text'][:250]}")
            except TimeoutError:
                safe_print("  ...still waiting...")
        if not got_tool:
            safe_print("  FAIL - model did not call screenshot")
        if not got_reply:
            safe_print("  FAIL - no AI reply received")

        await asyncio.sleep(5.0)
        await ws.close()

        # ── Test 4: NL → browser open ─────────────────────────────────────────
        safe_print("\n[TEST 4] Natural language -> open Firefox/browser")
        async with websockets.connect(URI) as ws_browser:
            init_browser = json.loads(await asyncio.wait_for(ws_browser.recv(), 10))
            safe_print(f"  isolated session provider={init_browser.get('provider')} model={init_browser.get('model')}")
            await prepare_session(ws_browser, mode="operator")
            await ws_browser.send(
                json.dumps(
                    {"type": "input", "text": "open google.com in the browser"}
                )
            )
            got_tool = False
            got_reply = False
            deadline = asyncio.get_running_loop().time() + 60
            while asyncio.get_running_loop().time() < deadline and not got_reply:
                try:
                    raw = await asyncio.wait_for(ws_browser.recv(), 8)
                    m = json.loads(raw)
                    t = m.get("type", "")
                    if t == "state":
                        safe_print(f"  state -> {m['state']}")
                    elif t == "action" and m.get("action") in {"browser_open", "run_command"}:
                        got_tool = True
                        safe_print(f"  TOOL CALLED: {m['action']} -> {str(m['result'])[:80]}")
                    elif t == "transcript" and m.get("role") == "assistant":
                        got_reply = True
                        safe_print(f"  AI REPLY: {m['text'][:250]}")
                    elif t == "error":
                        safe_print(f"  ERROR: {m.get('message', '')[:250]}")
                except TimeoutError:
                    safe_print("  ...waiting...")
            if not got_tool:
                safe_print("  FAIL - model did not call browser tool")
            if not got_reply:
                safe_print("  FAIL - no AI reply received")

        await asyncio.sleep(2.0)

        # ── Test 5: list_files ─────────────────────────────────────────────────
        safe_print("\n[TEST 5] list_files (Desktop)")
        async with websockets.connect(URI) as ws_files:
            await asyncio.wait_for(ws_files.recv(), 10)
            await prepare_session(ws_files)
            await ws_files.send(
                json.dumps(
                    {"type": "execute_tool", "tool": "list_files", "args": {}}
                )
            )  # no path → server resolves via winreg
            list_files_action = None
            deadline = asyncio.get_running_loop().time() + 20
            while asyncio.get_running_loop().time() < deadline and list_files_action is None:
                try:
                    raw = await asyncio.wait_for(ws_files.recv(), 5)
                except TimeoutError:
                    safe_print("  ...waiting for list_files...")
                    continue
                m = json.loads(raw)
                if m.get("type") == "action" and m.get("action") == "list_files":
                    list_files_action = m
                elif m.get("type") == "error":
                    safe_print(f"  ERROR: {m.get('message', '')[:250]}")
            if list_files_action:
                lines = list_files_action["result"].strip().split("\n")
                safe_print(f"  PASS - {len(lines)} items on Desktop")
                safe_print(f"  First 3: {', '.join(lines[:3])}")
            else:
                safe_print("  FAIL - no list_files action received")

        safe_print("\n=== All tests complete ===")

if __name__ == "__main__":
    asyncio.run(main())
