# 🧠 Vision Project - Complete Knowledge Base

**Last Updated**: May 14, 2026 05:15 AM  
**Purpose**: Comprehensive understanding of Vision's architecture, features, models, and configuration

---

## 📊 **Project Overview**

### **Mission**
Voice-first computer control system designed for accessibility, enabling disabled users to operate computers entirely through voice and natural language.

### **Core Philosophy**
- **Hands-free first**: No physical interaction required
- **Local-first**: Privacy and speed via local models
- **Multi-provider**: Cloud fallbacks for reliability
- **Always learning**: Elite brain adapts from user interactions

---

## 🏗️ **Architecture Deep Dive**

### **Backend Stack** (`live_chat_app.py`)

#### **FastAPI Server**
- **Port**: 8765
- **Host**: 127.0.0.1 (configurable via `VISION_HOST`)
- **Routes**: 46 registered endpoints
- **WebSocket**: Real-time bidirectional communication
- **CORS**: Configured origins from `VISION_ALLOWED_ORIGINS`

#### **Voice Pipeline**
```python
# Audio Input
SR = 16000  # Sample rate (Hz)
FRAME = 480  # Frame size (~30ms)
CHANNELS = 1  # Mono

# VAD (Voice Activity Detection)
RMS_THRESH = 500        # Volume threshold to start recording
START_FRAMES = 3        # Frames needed to trigger (~90ms)
END_FRAMES = 20         # Silence frames to stop (~600ms)
MIN_UTTERANCE_FRAMES = 6  # Minimum speech length (~180ms)

# Barge-in (Interrupt TTS)
BARGE_RMS = 1100        # Louder threshold to interrupt
BARGE_FRAMES = 4        # Frames needed to barge
```

#### **STT (Speech-to-Text) Cascade**

**When `preferred_stt = "local"` (Current)**:
1. **faster_whisper** (Primary)
   - Model: `tiny`
   - Device: `cpu`
   - Compute: `int8`
   - Language: `en`
   - Speed: ~500ms
   - Cost: Free
   - Privacy: Local

2. **ElevenLabs** (Fallback 1)
   - Model: `scribe_v1`
   - Speed: ~1-2s
   - Cost: API usage
   - Privacy: Cloud

3. **Groq** (Fallback 2)
   - Model: `whisper-large-v3-turbo`
   - Speed: ~1s
   - Cost: Free tier available
   - Privacy: Cloud

**When `preferred_stt = "auto"`**:
- If `continuous_listening = True`: Local → ElevenLabs → Groq
- If `continuous_listening = False`: ElevenLabs → Groq → Local

#### **TTS (Text-to-Speech)**
- **Provider**: ElevenLabs
- **Voice ID**: `0iuMR9ISp6Q7mg6H70yo` (Hitch/Ultron)
- **Model**: `eleven_flash_v2_5`
- **Rate**: 175 WPM (50-400 configurable)
- **Pitch**: 50 (0-100 configurable)

---

## 🤖 **LLM Provider Architecture**

### **Provider Registry**

#### **1. Ollama (Local)** ✅ Active
```python
{
    "label": "Ollama (Local)",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "models": []  # Populated at runtime via ollama.list()
}
```

**Configuration**:
- `OLLAMA_HOST`: `0.0.0.0:11434` (listening on all interfaces)
- `OLLAMA_MODELS`: `F:\models` (custom model storage)

**Available Models** (from `ollama list`):
- `cogito:latest` (Currently active)
- `deepseek-r1:1.5b`, `deepseek-r1:7b`, `deepseek-r1:8b`, `deepseek-r1:14b`, `deepseek-r1:32b`, `deepseek-r1:70b`
- `qwen2.5-coder:0.5b`, `qwen2.5-coder:1.5b`, `qwen2.5-coder:3b`, `qwen2.5-coder:7b`, `qwen2.5:14b`
- `llama3.2:latest`, `llama3.1:8b`
- `gemma3:12b`
- `mistral:7b`, `mistral-nemo:12b`, `mistral-small3.2:latest`
- `qwen3-coder:480b-cloud`
- `llava:13b` (Vision model)
- `wizardlm2:7b`, `openchat:7b`
- `falcon3:7b`
- `exaone-deep:7.8b`
- `gpt-oss:20b`
- Custom: `gerard/ultron:latest`, `qikfox/Eleven:latest`, `HammerAI/omega-darker-final-directive:latest`

#### **2. OpenAI** ✅ Active
```python
{
    "base_url": "https://api.openai.com/v1",
    "models": ["gpt-4.1", "gpt-4o", "o3", "o4-mini", ...]
}
```

#### **3. GitHub Models** ✅ Active
```python
{
    "base_url": "https://models.inference.ai.azure.com",
    "models": [
        "gpt-4.1", "o3", "o4-mini",
        "claude-3-7-sonnet-20250219",
        "Meta-Llama-3.3-70B-Instruct",
        ...
    ]
}
```

#### **4. DeepSeek** ✅ Active
```python
{
    "base_url": "https://api.deepseek.com/v1",
    "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"]
}
```

#### **5. Gemini** ✅ Active
```python
{
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
    "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash-lite"]
}
```

#### **6. NVIDIA** ✅ Active
```python
{
    "base_url": "https://integrate.api.nvidia.com/v1",
    "models": ["nvidia/llama-3.1-nemotron-70b-instruct", ...]
}
```

#### **7. Anthropic** ❌ Not Configured
- No API key set
- Models available: Claude Opus 4.5, Sonnet 4.5, etc.

#### **8. Groq** ❌ Not Configured
- No API key set
- Fast inference available for Llama, Gemma, DeepSeek models

---

## 💾 **Model Storage Architecture**

### **Primary Model Directory**: `F:\models`

#### **Ollama Models** (`F:\models\ollama-models`)
- **Type**: Ollama blob storage
- **Structure**: SHA256 blobs + manifests
- **Models**: All Ollama models listed above
- **Size**: ~200+ GB (estimated from model list)

#### **LM Studio Models** (`F:\models\lmstudio-community`)
- **Format**: GGUF (quantized)
- **Notable Models**:
  - `Phi-4-mini-reasoning-GGUF`
  - `Mistral-Nemo-Instruct-2407-GGUF`
  - `Qwen3-VL-4B-Instruct-GGUF`
  - `gemma-4-26B-A4B-it-GGUF`
  - `granite-3.2-8b-instruct-GGUF`
  - `Ministral-3-14B-Reasoning-2512-GGUF`
  - `NVIDIA-Nemotron-3-Nano-4B-GGUF`

#### **Msty Models** (`F:\models\msty-models`)
- **Structure**: Organized by creator
  - `bartowski/` - Community quantizations
  - `DavidAU/` - Custom fine-tunes
  - `mradermacher/` - GGUF quantizations
  - `unsloth/` - Fast fine-tuned models

#### **HuggingFace Cache** (`F:\models\models--*`)
- `models--google-bert--bert-base-uncased`
- `models--hexgrad--Kokoro-82M` (TTS model)
- `models--microsoft--Phi-3-vision-128k-instruct`
- `models--openai--clip-vit-base-patch32`
- `models--openai-community--gpt2`

#### **Specialized Directories**
- `F:\models\FastVLM-0.5B` - Vision-language model
- `F:\models\Phi-4-mini-instruct-onnx` - ONNX optimized
- `F:\models\mistral-7b-instruct-v0.2-ONNX` - ONNX format
- `F:\models\liquid` / `F:\models\LiquidAI` - Liquid AI models
- `F:\models\ibm` - IBM Granite models
- `F:\models\qwen` - Qwen model family
- `F:\models\ultra` - Ultra models

---

## 🧠 **Elite AI Modules**

### **1. Elite Brain** (`elite_brain.py`)
**Purpose**: Learning and adaptation from user interactions

**Current Stats** (from `/api/health`):
- **Semantic Memories**: 341
- **Episodes**: 341
- **Success Rate**: 94.1%
- **Active Tasks**: 59
- **Adaptation Rules**: 72
- **Curiosity Running**: ✅ Yes
- **LLM Wired**: ✅ Yes

**Key Features**:
- Episode tracking with success/failure outcomes
- Adaptation rule generation from patterns
- Semantic memory storage
- Curiosity-driven exploration

### **2. Elite Goals** (`elite_goals.py`)
**Purpose**: Goal prioritization and tracking

**Features**:
- Goal lifecycle management (created → active → completed/failed)
- Priority levels (critical, high, normal, low)
- Success criteria validation
- Action step tracking

### **3. Elite World** (`elite_world.py`)
**Purpose**: Entity state modeling and world awareness

**Features**:
- Entity type tracking (process, file, window, web_page, etc.)
- State snapshots
- Relationship mapping
- Real-time state updates

---

## 🔧 **Configuration Files**

### **Environment Variables** (`.env`)
```bash
# LLM Providers
OPENAI_API_KEY=<set>
GITHUB_TOKEN=<set>
DEEPSEEK_API_KEY=<set>
GEMINI_API_KEY=<set>
# ANTHROPIC_API_KEY=<not set>
# GROQ_API_KEY=<not set>

# Voice/TTS
ELEVENLABS_API_KEY=<set>

# Ollama
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_MODELS=F:\models

# Vision
VISION_BASE_URL=http://localhost:8765
VISION_HOST=127.0.0.1
PYTHONPATH=c:\project\vision
```

### **Memory State** (`memory.json`)
```json
{
  "context_summary": "AI language model for translation/interpretation",
  "voice": {
    "continuous_listening": true,  // ✅ FIXED (was false)
    "wake_word": false
  },
  "tasks": [
    // Recent task history (20 most recent)
  ]
}
```

### **Command Center Config** (`vision_command_center_config.json`)
```json
{
  "version": "1.0.0",
  "display_name": "Vision Command Center",
  "theme": "dark",
  "features": {
    "doctor": true,
    "context_brain": true,
    "routines": true,
    "missions": true
  }
}
```

---

## 🎯 **Key Features**

### **1. Voice Control**
- ✅ Continuous listening (always-on mode)
- ✅ Local STT (faster_whisper)
- ✅ Wake word support ("hey vision")
- ✅ Barge-in (interrupt TTS)
- ✅ Voice rate control (50-400 WPM)

### **2. Computer Control**
- ✅ PyAutoGUI integration (mouse/keyboard)
- ✅ Window management (win32gui)
- ✅ Screen capture & OCR (pytesseract)
- ✅ Web browser control
- ✅ Application launching

### **3. RAG Knowledge Base**
- ✅ SQLite FTS5 indexing
- ✅ Source: `F:\rag-v1\data` (default)
- ✅ Supported formats: .txt, .md, .py, .json, .yaml, etc.
- ✅ Search & retrieval
- ✅ Export capabilities

### **4. MCP Integration**
- ✅ MCP server (`vision_mcp_server.py`)
- ✅ Health, models, metrics, memory endpoints
- ✅ Screenshot + OCR tool
- ✅ External tool calling

### **5. Multi-Provider LLM**
- ✅ 6 active providers (Ollama, OpenAI, GitHub, DeepSeek, Gemini, NVIDIA)
- ✅ Automatic model listing (Ollama)
- ✅ Dynamic model switching
- ✅ Streaming responses

### **6. Accessibility**
- ✅ High contrast mode
- ✅ Keyboard navigation
- ✅ Screen reader compatible
- ✅ Voice rate/pitch control
- ✅ Hands-free operation

---

## 📁 **File Structure**

### **Core Backend**
- `live_chat_app.py` - Main FastAPI server (7,600+ lines)
- `vision_runtime.py` - Config & state management
- `vision_admin.py` - JWT auth & RBAC
- `vision_openclaw_bridge.py` - OpenClaw integration

### **Desktop GUI**
- `vision_hotkey.py` - Hotkey daemon (Ctrl+Alt+V)
- `voice_overlay.py` - Tkinter floating HUD
- `voice_cli.py` - CLI voice interface
- `voice_toggle.py` - Voice mode toggle

### **Web Interfaces**
- `live_chat_ui.html` - Main operator UI
- `live_chat_ui_v3.html` - Latest UI version
- `vision_command_center.html` - Diagnostics & control
- `rag_ui.html` - RAG interface

### **Elite AI Modules**
- `elite_brain.py` - Learning & adaptation
- `elite_goals.py` - Goal tracking
- `elite_world.py` - Entity modeling
- `elite_tools.py` - Tool execution
- `elite_voice.py` - Voice utilities
- `elite_memory.py` - Memory management
- `elite_patterns.py` - Pattern recognition
- `elite_resilience.py` - Error recovery
- `elite_safety.py` - Safety checks
- `elite_metrics.py` - Performance tracking

### **RAG System**
- `vision_rag.py` - SQLite FTS5 indexing
- `vision_rag_integration.py` - Pipeline
- `vision_rag_external.py` - External knowledge
- `rag_engine.py` - RAG engine
- `rag_tool.py` - RAG tooling

### **MCP & Tools**
- `vision_mcp_server.py` - MCP bridge
- `hive_tools/context_mapper.py` - Context brain

### **Testing & Diagnostics**
- `vision_test_suite.py` - Automated tests (8/8 passing)
- `vision_voice_validation.py` - Voice hardware tests
- `test_voice_diagnostic.py` - Real-time voice monitor
- `diagnose_voice.py` - Voice diagnostics
- `test_*.py` - Various test files

### **Utilities**
- `vision_auto_enhancer.py` - Auto-enhancement
- `vision_production_orchestrator.py` - Production readiness
- `vision_voice_commands.py` - 45 voice commands
- `enable_continuous_voice.py` - Voice settings helper
- `seed_memory.py` - Memory initialization
- `speak.py` - TTS utility

---

## 🚀 **Startup Flow**

### **1. Backend Launch** (`python live_chat_app.py`)
```python
1. Load .env file
2. Initialize providers (Ollama, OpenAI, etc.)
3. Load memory.json
4. Fetch Ollama models via ollama.list()
5. Initialize Elite brain/goals/world
6. Start voice loop (VAD + STT)
7. Start WebSocket server
8. Register 46 API routes
9. Listen on port 8765
10. Print: "[operator] Ready  ollama/cogito:latest"
```

### **2. Voice Loop Startup**
```python
1. Create asyncio.Queue for audio frames
2. Start sounddevice.InputStream (16kHz, mono)
3. Initialize VAD
4. Set initial state ("listening" if continuous, else "idle")
5. Enter infinite loop:
   - Read audio frames
   - Calculate RMS volume
   - Broadcast volume to WebSocket clients
   - Run VAD detection
   - Trigger STT on speech end
   - Process with LLM
   - Generate TTS response
```

### **3. Web UI Connection**
```
1. User opens http://localhost:8765
2. HTML/CSS/JS loads
3. WebSocket connects to ws://localhost:8765/ws
4. Backend sends "init" message with state
5. UI displays mic status, models, settings
6. User can interact via text or voice
```

---

## 📊 **Current Runtime State**

### **Backend**
- **Status**: ✅ Running (since 12:33 AM, 5+ hours uptime)
- **PID**: 11616
- **Model**: ollama/cogito:latest
- **State**: listening
- **Continuous**: ✅ Enabled (fixed)
- **STT**: local (faster_whisper)
- **TTS**: ElevenLabs

### **Voice**
- **Mode**: Continuous listening
- **VAD**: Active
- **STT**: Local → ElevenLabs → Groq cascade
- **TTS**: ElevenLabs (Hitch voice, 175 WPM)

### **Elite Brain**
- **Memories**: 341
- **Episodes**: 341
- **Success**: 94.1%
- **Tasks**: 59 active
- **Rules**: 72 adaptations
- **Learning**: ✅ Active

### **Providers**
- ✅ Ollama (cogito:latest)
- ✅ OpenAI (gpt-4.1, o3, etc.)
- ✅ GitHub (multi-model)
- ✅ DeepSeek
- ✅ Gemini
- ✅ NVIDIA
- ❌ Anthropic (no key)
- ❌ Groq (no key)

---

## 🎯 **Usage Patterns**

### **Voice Commands**
```
"open chrome"
"click the start button"
"type hello world"
"scroll down"
"take a screenshot and describe it"
"what's on my screen"
"search for python tutorial"
"help me"
"maximize this window"
"close this tab"
```

### **Text Commands**
```
/clear - Clear chat history
/screenshot - Capture screen
/help - Show available commands
[Any natural language] - Send to LLM
```

### **API Endpoints**
```
GET  /                          - Serve web UI
GET  /api/health                - Health check
GET  /api/models                - List models by provider
POST /api/model                 - Switch model
GET  /api/memory                - Get memory state
POST /api/memory/fact           - Add memory
GET  /api/metrics               - Performance metrics
GET  /api/accessibility/settings - Get accessibility config
POST /api/accessibility/settings - Update accessibility
GET  /api/brain/status          - Elite brain status
GET  /command-center            - Command center UI
POST /api/command-center/routines/{id} - Run routine
POST /api/command-center/missions/{id} - Run mission
WebSocket /ws                   - Real-time communication
```

---

## 🔬 **Advanced Features**

### **1. Automation Missions**
- Autonomous Maintenance Sweep
- Prime Command Deck
- Runtime Resilience Loop

### **2. Context Brain** (`hive_tools/context_mapper.py`)
- Repository intelligence
- Code indexing
- Context-aware suggestions

### **3. ElevenLabs Conversational AI**
- Real-time voice conversation
- Agent mode with tools
- Client-side audio processing

### **4. Computer Vision**
- Screen OCR (pytesseract)
- Visual question answering (llava:13b)
- Screenshot analysis

### **5. Goal-Oriented Behavior**
- Autonomous goal pursuit
- Multi-step planning
- Success criteria validation
- Task decomposition

---

## 📈 **Performance Characteristics**

### **Latency**
- Local STT: ~500ms (faster_whisper)
- Cloud STT: ~1-2s (ElevenLabs/Groq)
- LLM (local): ~1-5s (depends on model size)
- LLM (cloud): ~500ms-2s (depends on provider)
- TTS: ~1-2s (ElevenLabs)

### **Resource Usage**
- Backend: ~300-500MB RAM
- Ollama: Variable (per model)
  - cogito:latest: ~5GB VRAM
  - deepseek-r1:70b: ~40GB VRAM
- faster_whisper: ~1GB RAM
- Total system: 8-16GB+ (depends on active models)

---

## 🎓 **Learning & Adaptation**

### **Elite Brain Learning Cycle**
```
User Input
  ↓
LLM Response
  ↓
User Feedback (implicit/explicit)
  ↓
Episode Recording
  ↓
Pattern Detection
  ↓
Adaptation Rule Generation
  ↓
Future Behavior Adjustment
```

### **Adaptation Examples** (from health check)
```json
{
  "trigger": "Thank you.",
  "guidance": "Cover the request end-to-end",
  "successes": 13,
  "failures": 1,
  "updated_at": 1777818395
}
```

---

## 🔐 **Security & Privacy**

### **Local-First Architecture**
- ✅ Voice processed locally (faster_whisper)
- ✅ Models run locally (Ollama)
- ✅ Data stays on-device (SQLite storage)
- ✅ Optional cloud fallback (ElevenLabs, OpenAI)

### **Authentication**
- JWT-based admin system
- Role-based access control (RBAC)
- API token support (`VISION_TOOL_TOKEN`)

### **API Key Management**
- Environment variables
- System keyring storage
- .env file backup
- Runtime key updates

---

## 📚 **Documentation Files Created**

1. `SYSTEM_STATUS_FRESH_START.md` - Current runtime state
2. `VOICE_FIX_SUMMARY.md` - Voice transcription fix
3. `VOICE_TROUBLESHOOTING.md` - Voice debugging guide
4. `PRODUCTION_READY_REPORT.md` - Birthday package summary
5. `FINAL_VALIDATION_SUMMARY.txt` - Test results
6. `PRODUCTION_CHECKLIST.md` - Readiness checklist
7. `BIRTHDAY_GIFT_GUIDE.md` - User setup guide
8. `VISION_PROJECT_KNOWLEDGE_BASE.md` - This file

---

## 🎯 **Next Steps for Enhancement**

### **Immediate Priorities**
1. Test voice transcription with user
2. Verify continuous listening works
3. Test model switching (Ollama models)
4. Validate computer control commands

### **Future Enhancements**
1. Enable Anthropic provider (add API key)
2. Enable Groq provider (add API key)
3. Expand voice command library (45 → 100+)
4. Integrate more Ollama models (70B, vision models)
5. Optimize VAD thresholds for user's voice
6. Train custom voice profiles
7. Add more automation missions
8. Expand RAG knowledge base

---

**Status**: ✅ **Fully Operational and Learning**

**Last Knowledge Update**: May 14, 2026 05:15 AM
