"""Quick tool interaction test for Vision operator."""
import asyncio, json, sys
import websockets

URI = "ws://localhost:8765/ws"

async def recv_until(ws, types, timeout=60):
    """Collect messages until one of the given types appears."""
    results = []
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(raw)
            t = msg.get("type","")
            results.append(msg)
            if t in types:
                return results
        except asyncio.TimeoutError:
            continue
    return results

async def main():
    async with websockets.connect(URI) as ws:
        # Init
        init = json.loads(await asyncio.wait_for(ws.recv(), 10))
        print(f"[INIT] provider={init.get('provider')} model={init.get('model')}")

        # ── Test 1: Direct screenshot ──────────────────────────────────────────
        print("\n[TEST 1] Direct screenshot tool")
        await ws.send(json.dumps({"type": "execute_tool", "tool": "screenshot", "args": {}}))
        msgs = await recv_until(ws, {"screenshot","action"}, timeout=15)
        for m in msgs:
            if m["type"] == "screenshot":
                print(f"  PASS - screenshot received ({len(m['data'])} b64 chars)")
            elif m["type"] == "state":
                print(f"  state -> {m['state']}")
            elif m["type"] == "action":
                print(f"  action: {m['action']} -> {str(m['result'])[:80]}")

        # ── Test 2: run_command ────────────────────────────────────────────────
        print("\n[TEST 2] run_command tool")
        await ws.send(json.dumps({"type": "execute_tool", "tool": "run_command",
                                  "args": {"command": "echo vision-tool-test"}}))
        msgs = await recv_until(ws, {"action"}, timeout=15)
        for m in msgs:
            if m["type"] == "action":
                print(f"  PASS - result: {m['result'].strip()}")

        # ── Test 3: NL → tool call (screenshot) ───────────────────────────────
        print("\n[TEST 3] Natural language -> screenshot tool call")
        print("  Sending: 'take a screenshot and tell me what you see'")
        await ws.send(json.dumps({"type": "input",
                                  "text": "take a screenshot and tell me what you see"}))
        got_tool = False
        got_reply = False
        deadline = asyncio.get_event_loop().time() + 120
        while asyncio.get_event_loop().time() < deadline and not got_reply:
            try:
                raw = await asyncio.wait_for(ws.recv(), 8)
                m = json.loads(raw)
                t = m.get("type","")
                if t == "state":
                    print(f"  state -> {m['state']}")
                elif t == "action":
                    got_tool = True
                    print(f"  TOOL CALLED: {m['action']} -> {str(m['result'])[:80]}")
                elif t == "screenshot":
                    got_tool = True
                    print(f"  SCREENSHOT sent to UI ({len(m['data'])} b64 chars)")
                elif t == "transcript" and m.get("role") == "assistant":
                    got_reply = True
                    print(f"  AI REPLY: {m['text'][:250]}")
            except asyncio.TimeoutError:
                print("  ...still waiting...")
        if not got_tool:
            print("  FAIL - model did not call any tool")
        if not got_reply:
            print("  FAIL - no AI reply received")

        # ── Test 4: NL → browser open ─────────────────────────────────────────
        print("\n[TEST 4] Natural language -> open Firefox/browser")
        await ws.send(json.dumps({"type": "input",
                                  "text": "open google.com in the browser"}))
        got_tool = False
        got_reply = False
        deadline = asyncio.get_event_loop().time() + 60
        while asyncio.get_event_loop().time() < deadline and not got_reply:
            try:
                raw = await asyncio.wait_for(ws.recv(), 8)
                m = json.loads(raw)
                t = m.get("type","")
                if t == "state":
                    print(f"  state -> {m['state']}")
                elif t == "action":
                    got_tool = True
                    print(f"  TOOL CALLED: {m['action']} -> {str(m['result'])[:80]}")
                elif t == "transcript" and m.get("role") == "assistant":
                    got_reply = True
                    print(f"  AI REPLY: {m['text'][:250]}")
            except asyncio.TimeoutError:
                print("  ...waiting...")
        if not got_tool:
            print("  FAIL - model did not call browser tool")

        # ── Test 5: list_files ─────────────────────────────────────────────────
        print("\n[TEST 5] list_files (Desktop)")
        await ws.send(json.dumps({"type": "execute_tool", "tool": "list_files",
                                  "args": {}}))  # no path → server resolves via winreg
        msgs = await recv_until(ws, {"action"}, timeout=10)
        for m in msgs:
            if m["type"] == "action":
                lines = m["result"].strip().split("\n")
                print(f"  PASS - {len(lines)} items on Desktop")
                print(f"  First 3: {', '.join(lines[:3])}")

        print("\n=== All tests complete ===")

asyncio.run(main())
