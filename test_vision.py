"""
test_vision.py — Full integration test for Vision accessibility operator
Tests: HTTP, WebSocket, Ollama chat, tool execution, STT, TTS, Firefox
"""
import asyncio, json, time, sys, os, tempfile
import numpy as np
from scipy.io import wavfile

BASE = 'http://localhost:8765'
WS   = 'ws://localhost:8765/ws'
RESULTS = []

def ok(label, detail=''):
    RESULTS.append(('PASS', label))
    print(f'  ✓ {label}' + (f'  [{detail}]' if detail else ''))

def fail(label, err=''):
    RESULTS.append(('FAIL', label))
    print(f'  ✗ {label}: {str(err)[:120]}')

def section(title):
    print(f'\n{"="*55}')
    print(f'  {title}')
    print('='*55)

# ─────────────────────────────────────────────────────────
# 1. HTTP endpoints
# ─────────────────────────────────────────────────────────
section('1. HTTP ENDPOINTS')
import urllib.request

try:
    r = urllib.request.urlopen(f'{BASE}/', timeout=5)
    assert r.status == 200
    ok('GET / returns 200')
except Exception as e:
    fail('GET /', e)

try:
    r = urllib.request.urlopen(f'{BASE}/api/models', timeout=10)
    d = json.loads(r.read())
    n = len(d['providers']['ollama']['models'])
    cur = f"{d['current_provider']}/{d['current_model']}"
    ok(f'GET /api/models — {n} Ollama models', cur)
    models = d['providers']['ollama']['models']
    print(f'     First 10 Ollama models: {models[:10]}')
    # Check key statuses
    for k, pdata in d['providers'].items():
        if k == 'ollama': continue
        status = 'KEY OK' if pdata.get('has_key') else 'NO KEY'
        print(f'     {k:12}: {status}')
except Exception as e:
    fail('GET /api/models', e)

# ─────────────────────────────────────────────────────────
# 2. WebSocket connect
# ─────────────────────────────────────────────────────────
section('2. WEBSOCKET')

async def test_ws():
    import websockets
    try:
        async with websockets.connect(WS, open_timeout=5) as ws:
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            msg = json.loads(raw)
            assert msg.get('type') == 'init'
            ok('WS connect + init received',
               f"provider={msg.get('provider')} model={msg.get('model')}")
    except Exception as e:
        fail('WebSocket init', e)

asyncio.run(test_ws())

# ─────────────────────────────────────────────────────────
# 3. Ollama LLM chat
# ─────────────────────────────────────────────────────────
section('3. OLLAMA CHAT')

async def test_ollama_chat():
    import websockets
    try:
        async with websockets.connect(WS, open_timeout=5) as ws:
            await ws.recv()  # consume init
            await ws.send(json.dumps({'type': 'input', 'text': 'Reply with exactly this text and nothing else: VISION_TEST_OK'}))
            deadline = time.time() + 45
            while time.time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg = json.loads(raw)
                    if msg.get('type') == 'transcript' and msg.get('role') == 'assistant':
                        text = msg.get('text', '')
                        ok('Ollama replied', text[:100])
                        return True
                    if msg.get('type') == 'state':
                        print(f'     state: {msg.get("state")}')
                except asyncio.TimeoutError:
                    print('     waiting for reply...')
            fail('Ollama chat', 'No reply within 45s')
            return False
    except Exception as e:
        fail('Ollama chat', e)
        return False

asyncio.run(test_ollama_chat())

# ─────────────────────────────────────────────────────────
# 4. Tool execution
# ─────────────────────────────────────────────────────────
section('4. TOOL EXECUTION')

async def run_tool(tool_name, args, timeout=15):
    import websockets
    try:
        async with websockets.connect(WS, open_timeout=5) as ws:
            await ws.recv()  # init
            await ws.send(json.dumps({'type': 'execute_tool', 'tool': tool_name, 'args': args}))
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg = json.loads(raw)
                    if msg.get('type') == 'action' and msg.get('action') == tool_name:
                        return str(msg.get('result', ''))
                except asyncio.TimeoutError:
                    pass
            return None
    except Exception as e:
        return f'ERROR: {e}'

async def test_tools():
    # run_command
    r = await run_tool('run_command', {'command': 'echo TOOL_TEST_OK'})
    if r is None:
        fail('tool:run_command', 'No response')
    elif 'TOOL_TEST_OK' in r:
        ok('tool:run_command echo', r.strip())
    else:
        fail('tool:run_command echo', r[:80])

    # list_files
    r = await run_tool('list_files', {})
    if r and 'ERROR' not in r:
        ok('tool:list_files Desktop', f'{len(r.splitlines())} items')
    else:
        fail('tool:list_files', r)

    # get_clipboard
    r = await run_tool('get_clipboard', {})
    if r is not None and 'ERROR' not in r:
        ok('tool:get_clipboard', repr(r[:60]))
    else:
        fail('tool:get_clipboard', r)

    # set_clipboard
    r = await run_tool('set_clipboard', {'text': 'VISION_CLIP_TEST'})
    if r and 'Copied' in r:
        ok('tool:set_clipboard', r)
    else:
        fail('tool:set_clipboard', r)

    # list_windows
    r = await run_tool('list_windows', {})
    if r and 'ERROR' not in r:
        wins = [l for l in r.splitlines() if l.strip()]
        ok('tool:list_windows', f'{len(wins)} open windows')
    else:
        fail('tool:list_windows', r)

    # screenshot
    r = await run_tool('screenshot', {})
    if r is not None:
        ok('tool:screenshot', r[:60])
    else:
        fail('tool:screenshot', 'No response')

    return True

asyncio.run(test_tools())

# ─────────────────────────────────────────────────────────
# 5. Open Firefox
# ─────────────────────────────────────────────────────────
section('5. FIREFOX LAUNCH')

async def test_firefox():
    print('     Attempting: start firefox')
    r = await run_tool('run_command', {'command': 'start firefox'}, timeout=10)
    if r is not None:
        ok('Firefox launch via run_command', repr(r[:60]))
    else:
        fail('Firefox run_command', 'No response')

    # Also test via browser_open (Playwright)
    print('     Attempting: browser_open https://www.google.com')
    r = await run_tool('browser_open', {'url': 'https://www.google.com'}, timeout=20)
    if r and 'ERROR' not in r:
        ok('browser_open (Playwright)', r)
    else:
        fail('browser_open (Playwright)', str(r)[:80])

asyncio.run(test_firefox())

# ─────────────────────────────────────────────────────────
# 6. STT — faster-whisper local
# ─────────────────────────────────────────────────────────
section('6. STT — LOCAL FASTER-WHISPER')

try:
    from faster_whisper import WhisperModel
    sr = 16000
    # Generate a 2s tone at 440Hz (simulated audio)
    t_arr = np.linspace(0, 2, sr * 2, dtype=np.float32)
    tone  = (np.sin(2 * np.pi * 440 * t_arr) * 16000).astype(np.int16)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        wavfile.write(f.name, sr, tone)
        fpath = f.name
    wm = WhisperModel('tiny', device='cpu', compute_type='int8')
    segs, info = wm.transcribe(fpath, beam_size=1, language='en')
    result = ' '.join(s.text for s in segs).strip()
    os.unlink(fpath)
    ok(f'STT: faster-whisper tiny loaded', f'lang={info.language} result={result!r}')
except Exception as e:
    fail('STT faster-whisper', e)

# Check ElevenLabs STT key
try:
    import keyring, os as _os
    k = _os.environ.get('ELEVENLABS_API_KEY', '') or keyring.get_password('operator', 'ELEVENLABS_API_KEY') or ''
    if k:
        ok('STT ElevenLabs key present', f'key={k[:8]}…')
    else:
        fail('STT ElevenLabs key', 'No key — will use local fallback')
except Exception as e:
    fail('STT ElevenLabs key check', e)

# ─────────────────────────────────────────────────────────
# 7. TTS — pyttsx3
# ─────────────────────────────────────────────────────────
section('7. TTS — LOCAL PYTTSX3')

try:
    import pyttsx3
    eng = pyttsx3.init()
    voices = eng.getProperty('voices') or []
    voice_names = [v.name for v in voices]
    eng.setProperty('rate', 175)
    eng.setProperty('volume', 1.0)
    eng.say('Vision test ok')
    eng.runAndWait()
    ok('TTS pyttsx3 spoke', ', '.join(voice_names[:4]))
except Exception as e:
    fail('TTS pyttsx3', e)

# ─────────────────────────────────────────────────────────
# 8. Ollama model tool calling (llama3.1 native FC)
# ─────────────────────────────────────────────────────────
section('8. OLLAMA NATIVE TOOL CALLING TEST')

async def test_ollama_tools():
    import websockets
    # Switch to llama3.1 which supports native function calling
    try:
        async with websockets.connect(WS, open_timeout=5) as ws:
            await ws.recv()
            # Switch to operator mode + llama3.1
            await ws.send(json.dumps({'type': 'set_model', 'provider': 'ollama', 'model': 'llama3.1:latest'}))
            await ws.send(json.dumps({'type': 'set_mode', 'mode': 'operator'}))
            await ws.send(json.dumps({'type': 'input', 'text': 'Run the echo command to output the word TOOLCALL_OK'}))
            deadline = time.time() + 60
            got_action = False
            got_reply  = False
            while time.time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg = json.loads(raw)
                    t = msg.get('type')
                    if t == 'action':
                        ok(f'Ollama tool call executed: {msg["action"]}', str(msg.get("result",""))[:60])
                        got_action = True
                    if t == 'transcript' and msg.get('role') == 'assistant':
                        ok('Ollama tool reply', msg.get('text','')[:80])
                        got_reply = True
                    if got_action and got_reply:
                        break
                    if t == 'state' and msg.get('state') == 'idle':
                        if not got_action and not got_reply:
                            print('     idle reached with no tool call/reply yet...')
                        else:
                            break
                except asyncio.TimeoutError:
                    print('     waiting...')
            if not got_action:
                fail('Ollama operator tool call', 'No tool action seen — model may not support native FC for this task')
    except Exception as e:
        fail('Ollama operator tool test', e)

asyncio.run(test_ollama_tools())

# ─────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────
print('\n' + '='*55)
passed = sum(1 for s, _ in RESULTS if s == 'PASS')
failed = sum(1 for s, _ in RESULTS if s == 'FAIL')
print(f'  TOTAL: {passed} PASSED  {failed} FAILED')
print('='*55)
for s, l in RESULTS:
    icon = '✓' if s == 'PASS' else '✗'
    print(f'  {icon} {l}')
