---
name: ultron-azure-ai
description: 'Deploy FastAPI applications with SLM sidecar extensions to Azure App Service. Use when deploying AI chatbots, Phi-4/Phi-3 models, or Azure AI infrastructure.'
license: 'MIT'
---

# Ultron Azure AI Deployment Skill

**Purpose:** Deploy and manage FastAPI-based AI applications with Small Language Model (SLM) sidecar extensions on Azure App Service.

## When to Use This Skill

Invoke Ultron when:
- Deploying a FastAPI app to Azure App Service with AI capabilities
- Setting up Phi-4 or Phi-3 sidecar extensions
- Building custom SLM containers for Azure
- Managing Azure AI infrastructure
- Troubleshooting Azure App Service + SLM deployments

## Prerequisites

- Azure CLI 2.50+
- PowerShell 7.0+ or Bash
- Azure subscription with active credits
- Git

## Quick Start

### Deploy with Phi-4 Sidecar
```powershell
# Interactive mode
.\ultron-agent.ps1 -Action interactive

# Direct deployment
.\ultron-agent.ps1 -Action deploy -AppName mychatbot -Model phi-4 -Sku P3MV3 -Verbose
```

### Deploy with Phi-3 (Cost-Optimized)
```powershell
.\ultron-agent.ps1 -Action deploy -AppName mychatbot -Model phi-3 -Sku P2MV3
```

### Verify Deployment
```powershell
.\ultron-agent.ps1 -Action verify -AppName mychatbot -ResourceGroup mychatbot-rg
```

### Stream Logs
```powershell
.\ultron-agent.ps1 -Action logs -AppName mychatbot -ResourceGroup mychatbot-rg -Follow
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure App Service                         │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │   FastAPI App       │    │   SLM Sidecar Extension     │ │
│  │   (Main Container)  │◄──►│   (Phi-4/Phi-3 ONNX)        │ │
│  │                     │    │   Port: 11434               │ │
│  │   - Chat endpoints  │    │   - OpenAI-compatible API   │ │
│  │   - Health checks   │    │   - Local inference         │ │
│  │   - Streaming       │    │                             │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
│           │                              │                   │
│           └──────────┬─────────────────┘                   │
│                      │                                      │
│              Gunicorn + Uvicorn Workers                    │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Workflows

### Workflow 1: New Deployment

1. **Prerequisites Check**
   ```powershell
   az --version
   az account show
   ```

2. **Clone Sample Repository**
   ```powershell
   git clone https://github.com/Azure-Samples/ai-slm-in-app-service-sidecar
   cd ai-slm-in-app-service-sidecar/use_sidecar_extension/fastapiapp
   ```

3. **Deploy App Service**
   ```powershell
   az webapp up --sku P3MV3
   az webapp config set --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app"
   ```

4. **Add Sidecar Extension**
   - Navigate to Azure Portal
   - App Service → Deployment Center → Sidecar Extensions
   - Add → AI: phi-4-q4-gguf
   - Wait for Running status

5. **Verify Deployment**
   ```powershell
   $url = az webapp show --query defaultHostName -o tsv
   Invoke-RestMethod -Uri "https://$url/health"
   ```

### Workflow 2: Custom SLM Container

1. **Download Model**
   ```bash
   huggingface-cli download microsoft/Phi-3-mini-4k-instruct-onnx --local-dir ./Phi-3-mini-4k-instruct-onnx
   ```

2. **Build Container**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["python", "model_api.py"]
   ```

3. **Push to ACR**
   ```powershell
   az acr login --name myregistry
   docker tag phi-3 myregistry.azurecr.io/phi-3:latest
   docker push myregistry.azurecr.io/phi-3:latest
   ```

4. **Configure Sidecar**
   - Image source: Azure Container Registry
   - Port: 8000
   - Name: phi-3-custom

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SLM_API_URL` | Sidecar endpoint | `http://localhost:11434/v1/chat/completions` |
| `SLM_MODEL` | Model name | `phi-4` |
| `SLM_MAX_TOKENS` | Max tokens | `2048` |
| `SLM_TEMPERATURE` | Temperature | `0.7` |

### Pricing Tiers

| Tier | vCPUs | Memory | Suitable For |
|------|-------|--------|--------------|
| P1V3 | 2 | 8 GB | Development, testing |
| P2MV3 | 4 | 16 GB | Phi-3 mini, low traffic |
| P3MV3 | 8 | 32 GB | Phi-4, production workloads |
| P4MV3 | 16 | 64 GB | High throughput |
| P5MV3 | 32 | 128 GB | Enterprise scale |

## SLM Service Integration

### Python FastAPI Integration
```python
import httpx
import json
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

class SLMService:
    def __init__(self):
        self.api_url = 'http://localhost:11434/v1/chat/completions'

    async def generate(self, prompt: str):
        request_payload = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "cache_prompt": False,
            "n_predict": 2048
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.api_url,
                json=request_payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            ) as response:
                async for line in response.aiter_lines():
                    if not line or line == "[DONE]":
                        continue
                    if line.startswith("data: "):
                        line = line.replace("data: ", "").strip()
                    try:
                        json_obj = json.loads(line)
                        if "choices" in json_obj:
                            delta = json_obj["choices"][0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

@app.post("/chat")
async def chat(request: ChatRequest):
    slm = SLMService()
    response_text = ""
    async for token in slm.generate(request.message):
        response_text += token
    return {"response": response_text}

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "phi-4"}
```

## Troubleshooting

### Issue: Sidecar Not Starting
**Symptoms:** App deploys but sidecar shows "Pending" or "Failed"

**Solutions:**
1. Verify SKU is Premium v3 (P2MV3 or higher)
2. Check resource quotas in subscription
3. Review deployment logs: `az webapp log tail`
4. Ensure sufficient memory (Phi-4 needs 8GB+)

### Issue: 502 Bad Gateway
**Symptoms:** HTTP 502 errors when accessing app

**Solutions:**
1. Wait 2-3 minutes for sidecar initialization
2. Check startup command is correct
3. Verify sidecar status in Portal
4. Review application logs

### Issue: Timeout Errors
**Symptoms:** Requests timeout after 30 seconds

**Solutions:**
1. Increase timeout in SLMService (60s recommended)
2. Check model is loaded (first request is slower)
3. Verify sufficient compute resources
4. Enable streaming for long responses

### Issue: Model Not Responding
**Symptoms:** Chat endpoint returns empty responses

**Solutions:**
1. Verify SLM_API_URL is correct
2. Check sidecar is Running in Portal
3. Test direct sidecar access
4. Review sidecar logs

## Gotchas

1. **First Request Delay:** Initial model load takes 30-60 seconds
2. **Memory Requirements:** Phi-4 requires P3MV3 minimum
3. **Cold Start:** Apps may have cold start latency
4. **Sidecar Updates:** Changes require full redeployment
5. **Local Testing:** Sidecar only available in Azure, not locally

## Integration with Vision/OpenClaw

### From OpenClaw Elite
```powershell
# Deploy via OpenClaw
openclaw run ultron-azure-deploy --app-name mybot --model phi-4
```

### From Vision Command Center
```powershell
# API endpoint
Invoke-RestMethod -Uri "http://localhost:8765/api/ultron/deploy" -Method Post -Body '{"appName":"mybot","model":"phi-4"}'
```

### Direct Invocation
```powershell
# PowerShell
.\ultron-agent.ps1 -Action deploy -AppName mybot -Verbose

# Bash (via WSL)
pwsh ./ultron-agent.ps1 -Action deploy -AppName mybot
```

## References

- [Azure Sample Repository](https://github.com/Azure-Samples/ai-slm-in-app-service-sidecar)
- [Azure App Service Sidecar Overview](https://learn.microsoft.com/en-us/azure/app-service/overview-sidecar)
- [FastAPI on App Service](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat/create)
- [Phi-3 Model on Hugging Face](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx)

## Version History

- **1.0.0** (2026-04-28): Initial release with Phi-4/Phi-3 support, BYO container workflow
