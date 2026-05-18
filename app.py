import logging
import os

import anthropic
import requests
from flask import Flask, jsonify, render_template_string, request, send_from_directory
from flask_cors import CORS
from openai import OpenAI

# --- PRODUCTION LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MultiverseCommandPro")

# --- CORE CONFIGURATION ---
app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    return OpenAI(api_key=api_key) if api_key else None


def get_anthropic_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key) if api_key else None


# --- ELITE CINEMATIC UI (ONE-SHOT MASTERPIECE) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MULTIVERSE COMMAND: ELITE EDITION</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Bangers&family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.5);
            --accent: #f43f5e;
            --bg-dark: #020617;
            --glass: rgba(15, 23, 42, 0.85);
            --border: rgba(255, 255, 255, 0.08);
        }

        * {
            scrollbar-width: thin;
            scrollbar-color: var(--primary) transparent;
            box-sizing: border-box;
        }

        *::-webkit-scrollbar { width: 4px; }
        *::-webkit-scrollbar-track { background: transparent; }
        *::-webkit-scrollbar-thumb { background-color: var(--primary); border-radius: 10px; }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: #e2e8f0;
            height: 100vh;
            margin: 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            background-image:
                radial-gradient(circle at 20% 20%, rgba(59, 130, 246, 0.1) 0%, transparent 40%),
                radial-gradient(circle at 80% 80%, rgba(244, 63, 94, 0.05) 0%, transparent 40%);
        }

        /* --- ELITE LAYOUT ENGINE --- */
        .app-container {
            display: grid;
            grid-template-columns: 480px 1fr;
            grid-template-rows: 80px 1fr 320px;
            height: 100vh;
            width: 100vw;
            gap: 1px;
            background: var(--border);
        }

        .header {
            grid-column: 1 / span 2;
            background: rgba(2, 6, 23, 0.95);
            backdrop-filter: blur(30px);
            display: flex;
            align-items: center;
            padding: 0 40px;
            border-bottom: 1px solid var(--border);
        }

        .sidebar {
            grid-column: 1;
            grid-row: 2 / span 2;
            background: #020617;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border);
            overflow: hidden;
        }

        .arena {
            grid-column: 2;
            grid-row: 2;
            background: #020617;
            position: relative;
            overflow: hidden;
        }

        .intelligence-feed {
            grid-column: 2;
            grid-row: 3;
            background: #020617;
            border-top: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* --- UI COMPONENTS --- */
        .logo {
            font-family: 'Bangers', cursive;
            font-size: 2.8rem;
            letter-spacing: 3px;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 15px rgba(59, 130, 246, 0.4));
        }

        .panel-header {
            padding: 20px 30px;
            background: rgba(255,255,255,0.02);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .panel-label {
            font-family: 'Orbitron', sans-serif;
            font-size: 0.7rem;
            font-weight: 900;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #64748b;
        }

        .scroll-container {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
        }

        /* --- CHARACTER ENGINE --- */
        .character {
            position: absolute;
            width: 110px;
            height: 150px;
            z-index: 10;
            display: flex;
            flex-direction: column;
            align-items: center;
            transition: left 1.5s cubic-bezier(0.23, 1, 0.32, 1), top 1.5s cubic-bezier(0.23, 1, 0.32, 1);
        }

        .chibi-body {
            position: relative;
            width: 90px;
            height: 110px;
            transform-style: preserve-3d;
        }

        .chibi-img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            filter: drop-shadow(0 15px 30px rgba(0,0,0,0.9));
        }

        @keyframes elite-float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(2deg); }
        }

        @keyframes elite-walk {
            0%, 100% { transform: translateY(0) scaleY(1); }
            50% { transform: translateY(-12px) scaleY(1.05); }
        }

        @keyframes jump-strike {
            0% { transform: scale(1) translateY(0); }
            20% { transform: scale(1.2) translateY(-150px) rotate(-10deg); }
            40% { transform: scale(0.9) translateY(0) rotate(15deg); }
            60% { transform: scale(1.6) rotate(0deg); filter: brightness(2) drop-shadow(0 0 60px #3b82f6); }
            100% { transform: scale(1) translateY(0); }
        }

        .character:not(.walking):not(.striking) .chibi-body { animation: elite-float 4s infinite ease-in-out; }
        .walking .chibi-body { animation: elite-walk 0.4s infinite ease-in-out; }
        .striking .chibi-body { animation: jump-strike 1s cubic-bezier(0.19, 1, 0.22, 1); }

        .active-aura {
            filter: drop-shadow(0 0 50px var(--primary)) brightness(1.3);
            z-index: 100 !important;
        }

        /* --- SPEECH BUBBLES --- */
        .bubble {
            position: absolute;
            background: rgba(255, 255, 255, 0.98);
            color: #020617;
            padding: 20px 25px;
            border-radius: 24px;
            font-size: 14px;
            font-weight: 800;
            max-width: 300px;
            bottom: 180px;
            left: 50%;
            transform: translateX(-50%) scale(0);
            box-shadow: 0 30px 60px rgba(0,0,0,0.8);
            opacity: 0;
            z-index: 200;
            transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            pointer-events: none;
            border: 2px solid var(--primary);
        }

        .bubble.active { transform: translateX(-50%) scale(1); opacity: 1; }

        /* --- FORMS & INPUTS --- */
        .hero-card {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 25px;
            margin-bottom: 25px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .hero-card:hover {
            border-color: var(--primary);
            background: rgba(15, 23, 42, 0.8);
            transform: translateY(-5px);
        }

        .input-group label {
            display: block;
            font-size: 0.65rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #475569;
            margin-bottom: 10px;
        }

        input, select, textarea {
            background: #020617 !important;
            border: 1px solid var(--border) !important;
            color: #f1f5f9 !important;
            border-radius: 12px !important;
            padding: 14px 18px !important;
            font-size: 0.85rem !important;
            width: 100%;
            outline: none;
            transition: all 0.2s;
        }

        input:focus, select:focus, textarea:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        }

        /* --- LOG ENTRIES --- */
        .log-entry {
            background: rgba(255, 255, 255, 0.02);
            border-left: 6px solid var(--primary);
            padding: 25px;
            border-radius: 16px;
            margin-bottom: 20px;
            font-family: 'Inter', sans-serif;
            animation: slide-in 0.5s ease-out;
        }

        @keyframes slide-in {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* --- BUTTONS --- */
        .btn {
            padding: 16px 32px;
            border-radius: 16px;
            font-weight: 900;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.75rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.4);
        }

        .btn-primary:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 20px 40px rgba(37, 99, 235, 0.6);
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #475569;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }

        .status-online { background: #22c55e; box-shadow: 0 0 15px rgba(34, 197, 94, 0.6); }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- HEADER -->
        <div class="header">
            <div class="logo">MULTIVERSE COMMAND</div>
            <div class="ml-auto flex items-center space-x-10">
                <div class="flex items-center space-x-3">
                    <div id="ollama-status" class="status-dot"></div>
                    <span class="text-[10px] font-black tracking-widest text-slate-500 uppercase">Ollama Link</span>
                </div>
                <button id="start-battle" class="btn btn-primary">Initiate Multiverse Clash</button>
            </div>
        </div>

        <!-- SIDEBAR -->
        <div class="sidebar">
            <div class="panel-header">
                <span class="panel-label">Agent Orchestration</span>
                <button id="add-hero" class="text-blue-400 hover:text-blue-300 font-black text-[10px] uppercase tracking-widest">+ Summon Hero</button>
            </div>
            <div class="scroll-container" id="hero-list">
                <!-- Hero Cards -->
            </div>
        </div>

        <!-- ARENA -->
        <div class="arena" id="battle-arena">
            <div id="arena-bg" class="absolute inset-0 opacity-20 pointer-events-none"></div>
            <!-- Characters -->
        </div>

        <!-- INTELLIGENCE FEED -->
        <div class="intelligence-feed">
            <div class="panel-header">
                <span class="panel-label">Intelligence Feed</span>
                <div class="flex items-center space-x-6">
                    <div class="flex flex-col">
                        <span class="text-[8px] font-black text-slate-600 uppercase mb-1">Entry Vector</span>
                        <input type="text" id="initial-prompt" class="!py-2 !px-4 !w-72 !text-[10px] !font-bold" placeholder="Universal Command...">
                    </div>
                    <div class="flex flex-col">
                        <span class="text-[8px] font-black text-slate-600 uppercase mb-1">Lead Agent</span>
                        <select id="start-hero" class="!py-2 !px-4 !w-48 !text-[10px] !font-black"></select>
                    </div>
                </div>
            </div>
            <div class="scroll-container" id="chat-log">
                <!-- Logs -->
            </div>
        </div>
    </div>

    <!-- TEMPLATES -->
    <template id="hero-card-template">
        <div class="hero-card">
            <div class="flex items-center justify-between mb-8">
                <div class="flex items-center space-x-5">
                    <div class="w-16 h-16 rounded-2xl bg-slate-950 border border-blue-500/20 p-2 shadow-inner">
                        <img src="" class="hero-icon w-full h-full object-contain">
                    </div>
                    <input type="text" class="hero-name !bg-transparent !border-none !p-0 !text-2xl !font-black !w-48" value="Hero">
                </div>
                <button class="remove-hero text-slate-700 hover:text-red-500 transition-colors">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
            </div>

            <div class="grid grid-cols-2 gap-6 mb-6">
                <div class="input-group">
                    <label>Origin Provider</label>
                    <select class="provider-select">
                        <option value="ollama">Ollama (Local)</option>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>Target Agent</label>
                    <select class="target-select">
                        <option value="">Cease Action</option>
                    </select>
                </div>
            </div>

            <div class="input-group mb-6">
                <label>Model Essence</label>
                <select class="model-select"></select>
            </div>

            <div class="input-group">
                <label>Mission Directives</label>
                <textarea class="system-prompt !h-24" placeholder="Define core behavior..."></textarea>
            </div>
        </div>
    </template>

    <script>
        const ROSTER = [
            { name: 'Spider-Man', color: '#f43f5e', img: '/hero_red_hd.png' },
            { name: 'Batman', color: '#475569', img: '/batman_hd.png' },
            { name: 'Wonder Woman', color: '#f59e0b', img: '/wonderwoman_hd.png' },
            { name: 'Iron Man', color: '#ef4444', img: '/hero_iron_hd.png' }
        ];

        let agents = [];
        let isRunning = false;

        function summonHero() {
            const id = 'agent_' + Math.random().toString(36).substr(2, 6);
            const baseData = ROSTER[agents.length % ROSTER.length];

            const template = document.getElementById('hero-card-template');
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('.hero-card');
            card.id = 'card-' + id;
            card.querySelector('.hero-icon').src = baseData.img;
            card.querySelector('.hero-name').value = baseData.name;

            const providerSelect = card.querySelector('.provider-select');
            const modelSelect = card.querySelector('.model-select');
            const targetSelect = card.querySelector('.target-select');
            const removeBtn = card.querySelector('.remove-hero');

            providerSelect.onchange = () => syncModels(providerSelect.value, modelSelect);
            removeBtn.onclick = () => {
                card.remove();
                document.getElementById('avatar-' + id).remove();
                agents = agents.filter(a => a.id !== id);
                refreshGlobalSelects();
            };

            document.getElementById('hero-list').appendChild(clone);
            syncModels('ollama', modelSelect);

            // Create Avatar
            const avatar = document.createElement('div');
            avatar.className = 'character';
            avatar.id = 'avatar-' + id;
            avatar.innerHTML = `
                <div class="bubble" id="bubble-${id}"></div>
                <div class="chibi-body">
                    <img src="${baseData.img}" class="chibi-img">
                </div>
                <div class="mt-4 bg-blue-600/20 border border-blue-500/30 px-5 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest backdrop-blur-md">${baseData.name}</div>
            `;
            avatar.style.left = (15 + Math.random() * 70) + '%';
            avatar.style.top = (15 + Math.random() * 60) + '%';
            document.getElementById('battle-arena').appendChild(avatar);

            agents.push({ id, baseData, card, avatar });
            refreshGlobalSelects();
        }

        async function syncModels(provider, select) {
            select.innerHTML = '<option value="">Synchronizing...</option>';
            try {
                const r = await fetch(`/api/models?provider=${provider}`);
                const d = await r.json();
                select.innerHTML = '';
                if (d.error) { select.innerHTML = '<option value="">Offline</option>'; return; }
                d.models.forEach(m => {
                    const o = document.createElement('option');
                    o.value = m.id; o.textContent = m.name;
                    select.appendChild(o);
                });
            } catch (e) { select.innerHTML = '<option value="">Failure</option>'; }
        }

        function refreshGlobalSelects() {
            const opts = agents.map(a => `<option value="${a.id}">${a.card.querySelector('.hero-name').value}</option>`).join('');
            document.querySelectorAll('.target-select').forEach(s => {
                const cur = s.value;
                s.innerHTML = '<option value="">Cease Action</option>' + opts;
                s.value = cur;
            });
            const startSelect = document.getElementById('start-hero');
            startSelect.innerHTML = opts;
        }

        async function moveTo(avatar, x, y) {
            avatar.classList.add('walking');
            avatar.style.left = x + '%';
            avatar.style.top = y + '%';
            await new Promise(r => setTimeout(r, 1500));
            avatar.classList.remove('walking');
        }

        async function triggerStrike(agent) {
            agent.avatar.classList.add('striking');
            await new Promise(r => setTimeout(r, 1000));
            agent.avatar.classList.remove('striking');
        }

        async function startClash() {
            if (isRunning) return;
            isRunning = true;
            document.getElementById('start-battle').textContent = 'CLASH IN PROGRESS';

            let currentId = document.getElementById('start-hero').value;
            let currentMsg = document.getElementById('initial-prompt').value;
            const log = document.getElementById('chat-log');
            log.innerHTML = '';

            while (currentId && isRunning) {
                const agent = agents.find(a => a.id === currentId);
                if (!agent) break;

                await moveTo(agent.avatar, 45, 35);
                agent.avatar.classList.add('active-aura');
                const bubble = document.getElementById(`bubble-${agent.id}`);
                bubble.textContent = "SYNCHRONIZING WITH MULTIVERSE...";
                bubble.classList.add('active');

                try {
                    const name = agent.card.querySelector('.hero-name').value;
                    const provider = agent.card.querySelector('.provider-select').value;
                    const model = agent.card.querySelector('.model-select').value;
                    const system = agent.card.querySelector('.system-prompt').value;

                    const r = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ provider, model, system, message: currentMsg })
                    });
                    const res = await r.json();

                    await triggerStrike(agent);
                    bubble.textContent = res.output.substring(0, 100) + "...";

                    const entry = document.createElement('div');
                    entry.className = 'log-entry';
                    entry.style.borderColor = agent.baseData.color;
                    entry.innerHTML = `
                        <div class="flex justify-between items-center mb-4">
                            <span class="font-black text-xl uppercase tracking-widest" style="color: ${agent.baseData.color}">${name}</span>
                            <span class="text-[9px] font-black bg-slate-900 px-4 py-1.5 rounded-full text-slate-500 border border-slate-800">${model}</span>
                        </div>
                        <div class="text-base leading-relaxed text-slate-300 font-medium">${res.output}</div>
                    `;
                    log.prepend(entry);

                    await new Promise(r => setTimeout(r, 4000));

                    bubble.classList.remove('active');
                    agent.avatar.classList.remove('active-aura');
                    await moveTo(agent.avatar, 10 + Math.random() * 80, 10 + Math.random() * 70);

                    currentMsg = res.output;
                    currentId = agent.card.querySelector('.target-select').value;
                } catch (e) { break; }
            }
            isRunning = false;
            document.getElementById('start-battle').textContent = 'Initiate Multiverse Clash';
        }

        async function monitorOllama() {
            const dot = document.getElementById('ollama-status');
            try {
                const r = await fetch('/api/models?provider=ollama');
                if (r.ok) dot.className = 'status-dot status-online';
                else dot.className = 'status-dot';
            } catch (e) { dot.className = 'status-dot'; }
        }

        document.getElementById('add-hero').onclick = summonHero;
        document.getElementById('start-battle').onclick = startClash;
        setInterval(monitorOllama, 5000);
        monitorOllama();

        // Initial Summons
        summonHero(); summonHero();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/<path:path>")
def serve_assets(path):
    return send_from_directory(app.static_folder, path)


@app.route("/api/models", methods=["GET"])
def fetch_models():
    provider = request.args.get("provider", "ollama")
    try:
        if provider == "ollama":
            r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            return jsonify({"models": [{"id": m["name"], "name": m["name"]} for m in r.json().get("models", [])]})
        elif provider == "openai":
            c = get_openai_client()
            if not c:
                return jsonify({"error": "Missing Key"}), 400
            return jsonify({"models": [{"id": m.id, "name": m.id} for m in c.models.list().data if "gpt" in m.id]})
        elif provider == "anthropic":
            if not get_anthropic_client():
                return jsonify({"error": "Missing Key"}), 400
            return jsonify({"models": [{"id": "claude-3-7-sonnet-20250219", "name": "Claude 3.7 Sonnet"}]})
        return jsonify({"models": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def handle_chat():
    d = request.json
    p, m, s, msg = d.get("provider"), d.get("model"), d.get("system", ""), d.get("message", "")
    try:
        if p == "ollama":
            r = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": m, "system": s, "prompt": msg, "stream": False},
                timeout=180,
            )
            return jsonify({"output": r.json().get("response", "")})
        elif p == "openai":
            client = get_openai_client()
            if client is None:
                return jsonify({"error": "OpenAI API key not configured"}), 400
            r = client.chat.completions.create(
                model=m, messages=[{"role": "system", "content": s}, {"role": "user", "content": msg}]
            )
            return jsonify({"output": r.choices[0].message.content})
        elif p == "anthropic":
            client = get_anthropic_client()
            if client is None:
                return jsonify({"error": "Anthropic API key not configured"}), 400
            r = client.messages.create(model=m, max_tokens=2048, system=s, messages=[{"role": "user", "content": msg}])
            return jsonify({"output": r.content[0].text})
        return jsonify({"error": f"Unsupported provider: {p}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("Starting Multiverse Command: Elite Masterpiece Edition...")
    app.run(host="127.0.0.1", port=5000, debug=False)
