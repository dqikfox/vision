# 🤖 Vision Model Library - Quick Reference

**Model Storage**: `F:\models` (OLLAMA_MODELS environment variable)  
**Ollama Host**: `0.0.0.0:11434`  
**Total Storage**: ~200+ GB across all model formats

---

## 📊 **Currently Available Ollama Models**

### **Active Model**
- ✅ **cogito:latest** (Currently running in Vision)

### **DeepSeek R1 Family** (Reasoning Models)
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| `deepseek-r1:1.5b` | 1.0 GB | ~2 GB | Fast reasoning, low-resource |
| `deepseek-r1:7b` | 4.7 GB | ~8 GB | Balanced reasoning |
| `deepseek-r1:8b` | 5.2 GB | ~8 GB | General reasoning |
| `deepseek-r1:14b` | 9.0 GB | ~14 GB | Advanced reasoning |
| `deepseek-r1:32b` | 19 GB | ~32 GB | High-capacity reasoning |
| `deepseek-r1:70b` | 43 GB | ~70 GB | Enterprise-grade reasoning |

### **Qwen Family** (Alibaba Cloud)
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| `qwen2.5-coder:0.5b` | 397 MB | ~1 GB | Ultra-fast coding assistant |
| `qwen2.5-coder:1.5b` | 986 MB | ~2 GB | Lightweight coding |
| `qwen2.5-coder:3b` | 1.9 GB | ~4 GB | Balanced coding |
| `qwen2.5-coder:7b` | 4.7 GB | ~8 GB | Advanced coding |
| `qwen2.5:14b` | 9.0 GB | ~14 GB | General purpose |
| `qwen2.5vl:latest` | 6.0 GB | ~10 GB | Vision-language (multimodal) |
| `qwen3-coder:480b-cloud` | - | Cloud | Massive cloud-based coding |

### **Meta Llama Family**
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| `llama3.2:latest` | 2.0 GB | ~4 GB | Lightweight, fast |
| `llama3.1:8b` | 4.9 GB | ~8 GB | General purpose |

### **Google Gemma Family**
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| `gemma3:12b` | 8.1 GB | ~12 GB | Advanced reasoning |
| `embeddinggemma:latest` | 621 MB | ~1 GB | Text embeddings |

### **Mistral AI Family**
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| `mistral:7b` | 4.4 GB | ~8 GB | Efficient general purpose |
| `mistral-nemo:12b` | 7.1 GB | ~12 GB | Advanced capabilities |
| `mistral-small3.2:latest` | 15 GB | ~24 GB | High-performance |
| `devstral:latest` | 14 GB | ~20 GB | Development-focused |

### **Vision Models**
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| `llava:13b` | 8.0 GB | ~16 GB | Image understanding + chat |
| `qwen2.5vl:latest` | 6.0 GB | ~10 GB | Vision-language tasks |

### **Specialized Models**
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| `wizardlm2:7b` | 4.1 GB | ~8 GB | Instruction following |
| `openchat:7b` | 4.1 GB | ~8 GB | Conversational AI |
| `falcon3:7b` | 4.6 GB | ~8 GB | General purpose |
| `exaone-deep:7.8b` | 4.8 GB | ~10 GB | Deep reasoning |
| `gpt-oss:20b` | 13 GB | ~20 GB | Open-source GPT alternative |

### **Custom/Community Models**
| Model | Size | Creator | Use Case |
|-------|------|---------|----------|
| `gerard/ultron:latest` | 4.7 GB | Custom | ULTRON personality |
| `qikfox/Eleven:latest` | 2.0 GB | Custom | ElevenLabs integration |
| `HammerAI/omega-darker-final-directive:latest` | 19 GB | Community | Advanced reasoning |
| `taozhiyuai/llama-3-8b-ultra-instruct:q4_k_m` | 4.9 GB | Community | Optimized Llama 3 |
| `NeuroEquality/neuralquantum-coder:latest` | 13 GB | Community | Quantum coding assistant |

---

## 📁 **LM Studio Models** (`F:\models\lmstudio-community`)

### **Microsoft Phi Family**
- `Phi-4-mini-reasoning-GGUF` - Reasoning-focused small model
- `Phi-3-vision-128k-instruct` (HuggingFace) - Vision + 128k context

### **Google Gemma**
- `gemma-3-4b-it-GGUF` - Instruction-tuned 4B
- `gemma-3n-E4B-it-text-GGUF` - Enhanced 4B
- `gemma-4-26B-A4B-it-GGUF` - Large variant
- `gemma-4-E2B-it-GGUF`, `gemma-4-E4B-it-GGUF` - Enhanced variants

### **Mistral/Ministral**
- `Mistral-Nemo-Instruct-2407-GGUF` - 12B instruct
- `Ministral-3-14B-Reasoning-2512-GGUF` - Reasoning-optimized
- `Ministral-3-3B-Instruct-2512-GGUF` - Small instruct

### **Alibaba Qwen**
- `Qwen3-4B-Thinking-2507-GGUF` - Thinking mode
- `Qwen3-VL-4B-Instruct-GGUF` - Vision-language
- `Qwen3.5-9B-GGUF` - Latest generation

### **NVIDIA**
- `NVIDIA-Nemotron-3-Nano-4B-GGUF` - Nano variant

### **IBM Granite**
- `granite-3.2-8b-instruct-GGUF` - Enterprise-grade

### **Specialized**
- `olmOCR-2-7B-1025-GGUF` - OCR-specialized
- `LFM2.5-1.2B-Instruct-GGUF` - Language foundation model
- `functiongemma-270m-it-GGUF` - Function calling
- `gpt-oss-20b-GGUF` - Open-source GPT
- `ERNIE-4.5-21B-A3B-PT-GGUF` - Baidu ERNIE

---

## 🎨 **Msty Models** (`F:\models\msty-models`)

Organized by creator:

### **bartowski/** - High-quality quantizations
- Expert quantizations of popular models
- Multiple quant levels (Q2_K to Q8_0)

### **DavidAU/** - Custom fine-tunes
- Specialized task models
- Domain-specific adaptations

### **mradermacher/** - GGUF quantizations
- Wide range of model sizes
- Performance-optimized quants

### **unsloth/** - Fast fine-tuned models
- Optimized for inference speed
- LoRA/QLoRA adaptations

---

## 🔬 **Specialized Model Collections**

### **Vision Models**
- `FastVLM-0.5B` - Ultra-lightweight vision-language
- `Phi-3-vision-128k-instruct` - Microsoft vision model
- `llava:13b` (Ollama) - Chat + image understanding
- `qwen2.5vl:latest` (Ollama) - Qwen vision-language

### **TTS Models**
- `Kokoro-82M` (HuggingFace) - Text-to-speech

### **Embedding Models**
- `embeddinggemma:latest` (Ollama) - 621 MB
- `bert-base-uncased` (HuggingFace) - Text embeddings
- `clip-vit-base-patch32` (HuggingFace) - Vision embeddings

### **ONNX Optimized**
- `Phi-4-mini-instruct-onnx` - Microsoft ONNX
- `mistral-7b-instruct-v0.2-ONNX` - Mistral ONNX

### **Liquid AI Models**
- `F:\models\liquid` - Liquid network models
- `F:\models\LiquidAI` - Advanced liquid models

---

## 🚀 **Model Switching in Vision**

### **Via Web UI**
```javascript
// UI automatically lists Ollama models
// Click model dropdown → select → switch
```

### **Via API**
```bash
curl -X POST http://localhost:8765/api/model \
  -H "Content-Type: application/json" \
  -d '{"provider":"ollama","model":"deepseek-r1:70b"}'
```

### **Via WebSocket**
```json
{
  "type": "set_model",
  "provider": "ollama",
  "model": "qwen2.5-coder:7b"
}
```

---

## 💡 **Model Recommendations by Use Case**

### **Voice Assistant** (Current)
- ✅ `cogito:latest` - Balanced, fast
- Alternative: `llama3.2:latest` - Lightweight, efficient

### **Coding Tasks**
1. `qwen2.5-coder:7b` - Best balance
2. `qwen2.5-coder:3b` - Fast coding
3. `qwen2.5-coder:0.5b` - Ultra-fast snippets
4. `deepseek-r1:14b` - Reasoning-based coding

### **Reasoning/Planning**
1. `deepseek-r1:70b` - Best reasoning (needs 70GB VRAM)
2. `deepseek-r1:32b` - High-capacity reasoning
3. `deepseek-r1:14b` - Balanced reasoning
4. `Phi-4-mini-reasoning-GGUF` - Efficient reasoning

### **Vision Tasks**
1. `llava:13b` - Best for chat + images
2. `qwen2.5vl:latest` - Vision-language tasks
3. `Phi-3-vision-128k-instruct` - Long context vision

### **Low-Resource**
1. `qwen2.5-coder:0.5b` - 397 MB, ultra-fast
2. `embeddinggemma:latest` - 621 MB, embeddings
3. `LFM2.5-1.2B-Instruct-GGUF` - 1.2B, general
4. `llama3.2:latest` - 2 GB, balanced

### **Enterprise/Production**
1. `deepseek-r1:70b` - Flagship reasoning
2. `mistral-small3.2:latest` - High-performance
3. `gpt-oss:20b` - Open-source GPT
4. `granite-3.2-8b-instruct-GGUF` - IBM enterprise

---

## 📊 **Storage Breakdown**

```
F:\models/
├── ollama-models/          ~100+ GB (Ollama blobs)
├── lmstudio-community/     ~50+ GB (GGUF models)
├── msty-models/            ~30+ GB (Quantized models)
├── HuggingFace cache/      ~10+ GB (transformers)
├── Specialized/            ~10+ GB (ONNX, Liquid, etc.)
└── Total:                  ~200+ GB
```

---

## 🔧 **Ollama Management**

### **List Models**
```bash
ollama list
```

### **Pull New Model**
```bash
ollama pull deepseek-r1:70b
```

### **Run Model**
```bash
ollama run cogito:latest
```

### **Remove Model**
```bash
ollama rm mistral:7b
```

### **Model Info**
```bash
ollama show cogito:latest
```

---

## 🎯 **Quick Model Selection Guide**

**Need speed?** → `qwen2.5-coder:0.5b`, `llama3.2:latest`  
**Need reasoning?** → `deepseek-r1:14b`, `deepseek-r1:32b`  
**Need coding?** → `qwen2.5-coder:7b`, `deepseek-r1:14b`  
**Need vision?** → `llava:13b`, `qwen2.5vl:latest`  
**Need efficiency?** → `gemma3:12b`, `mistral-nemo:12b`  
**Need power?** → `deepseek-r1:70b`, `gpt-oss:20b`  

---

**Last Updated**: May 14, 2026 05:20 AM  
**Total Models Available**: 50+ Ollama + 30+ LM Studio + Msty collections  
**Storage**: F:\models (OLLAMA_MODELS)
