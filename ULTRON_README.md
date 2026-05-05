# ⚡ Ultron — Azure AI Deployment Agent

**Ultron** is an elite Azure AI deployment specialist that automates the deployment of FastAPI applications with Small Language Model (SLM) sidecar extensions on Azure App Service.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![PowerShell](https://img.shields.io/badge/powershell-7+-blue)
![Azure](https://img.shields.io/badge/azure-app%20service-blue)

---

## 🚀 Quick Start

```powershell
# Interactive mode (recommended for first use)
.\ultron-agent.ps1 -Action interactive

# Deploy with Phi-4 sidecar
.\ultron-agent.ps1 -Action deploy -AppName mychatbot -Model phi-4 -Verbose

# Deploy with Phi-3 (cost-optimized)
.\ultron-agent.ps1 -Action deploy -AppName mychatbot -Model phi-3 -Sku P2MV3
```

---

## ✨ Features

- **🤖 Automated Deployment** — One-command deployment of FastAPI + SLM apps
- **🧠 Phi-4/Phi-3 Support** — Built-in support for Microsoft's SLM models
- **📦 BYO Container** — Build and deploy custom SLM containers
- **🔍 Smart Verification** — Automatic health checks and endpoint testing
- **📊 Log Streaming** — Real-time log monitoring
- **🧹 Easy Cleanup** — One-command resource destruction
- **🎨 Interactive UI** — Beautiful ASCII art and color-coded output

---

## 📋 Prerequisites

- **Azure CLI** 2.50+ — [Install](https://aka.ms/installazurecliwindows)
- **PowerShell** 7.0+ — [Install](https://github.com/PowerShell/PowerShell/releases)
- **Azure Subscription** — [Free trial](https://azure.microsoft.com/free)
- **Git** — [Install](https://git-scm.com/download/win)

---

## 🏗️ Architecture

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

---

## 📖 Usage Guide

### 1. Deploy a New Application

```powershell
# Basic deployment
.\ultron-agent.ps1 -Action deploy -AppName mychatbot

# With custom settings
.\ultron-agent.ps1 -Action deploy `
    -AppName mychatbot `
    -ResourceGroup mychatbot-rg `
    -Location eastus `
    -Sku P3MV3 `
    -Model phi-4 `
    -Verbose
```

### 2. Verify Deployment

```powershell
.\ultron-agent.ps1 -Action verify -AppName mychatbot -ResourceGroup mychatbot-rg
```

### 3. Stream Logs

```powershell
# Follow logs in real-time
.\ultron-agent.ps1 -Action logs -AppName mychatbot -ResourceGroup mychatbot-rg -Follow

# Show last 60 seconds
.\ultron-agent.ps1 -Action logs -AppName mychatbot -ResourceGroup mychatbot-rg
```

### 4. Build Custom SLM Container

```powershell
# Build locally
.\ultron-agent.ps1 -Action byo-build -CustomImage my-phi3-model

# Build and push to ACR
.\ultron-agent.ps1 -Action byo-build -CustomImage my-phi3-model -AcrName myregistry
```

### 5. Check Status

```powershell
# List all Ultron deployments
.\ultron-agent.ps1 -Action status

# Check specific resource group
.\ultron-agent.ps1 -Action status -ResourceGroup mychatbot-rg
```

### 6. Cleanup

```powershell
# Destroy all resources (irreversible!)
.\ultron-agent.ps1 -Action destroy -ResourceGroup mychatbot-rg
```

---

## 💰 Pricing Tiers

| Tier | vCPUs | Memory | Best For | Monthly Cost* |
|------|-------|--------|----------|---------------|
| P1V3 | 2 | 8 GB | Development | ~$73 |
| P2MV3 | 4 | 16 GB | Phi-3, Testing | ~$146 |
| **P3MV3** | **8** | **32 GB** | **Phi-4, Production** | **~$292** |
| P4MV3 | 16 | 64 GB | High Throughput | ~$585 |
| P5MV3 | 32 | 128 GB | Enterprise | ~$1,170 |

*Approximate costs, varies by region

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file for persistent settings:

```env
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_DEFAULT_LOCATION=eastus
AZURE_DEFAULT_SKU=P3MV3
ULTRON_DEFAULT_MODEL=phi-4
```

### Startup Command

Default Gunicorn configuration:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

Customize with:
```powershell
.\ultron-agent.ps1 -Action deploy -StartupFile "gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app"
```

---

## 🐛 Troubleshooting

### Sidecar Not Starting

**Symptoms:** Sidecar shows "Pending" or "Failed"

**Solutions:**
1. ✅ Verify SKU is Premium v3 (P2MV3 or higher)
2. ✅ Check Azure subscription has sufficient quota
3. ✅ Review logs: `az webapp log tail --name myapp --resource-group myrg`
4. ✅ Ensure sufficient memory (Phi-4 needs 8GB+)

### 502 Bad Gateway

**Symptoms:** HTTP 502 errors

**Solutions:**
1. ⏱️ Wait 2-3 minutes for sidecar initialization
2. 🔧 Verify startup command is correct
3. 📊 Check sidecar status in Azure Portal
4. 📄 Review application logs

### Timeout Errors

**Symptoms:** Requests timeout after 30 seconds

**Solutions:**
1. ⏱️ Increase timeout to 60 seconds
2. 🧠 First request loads model (slower)
3. 💪 Verify sufficient compute resources
4. 🌊 Enable streaming for long responses

---

## 🔗 Integration

### OpenClaw Elite

```powershell
# Add to OpenClaw Elite menu
# Edit openclaw-elite.ps1 and add:

"12" {
    Write-Host "⚡ Launching Ultron Azure AI Agent..."
    .\ultron-agent.ps1 -Action interactive
}
```

### Vision Command Center

```powershell
# API endpoint for Vision integration
Invoke-RestMethod -Uri "http://localhost:8765/api/ultron/deploy" -Method Post -Body '{
    "appName": "mybot",
    "model": "phi-4",
    "sku": "P3MV3"
}'
```

---

## 📚 References

- [Azure Sample Repository](https://github.com/Azure-Samples/ai-slm-in-app-service-sidecar)
- [Azure App Service Sidecar Overview](https://learn.microsoft.com/en-us/azure/app-service/overview-sidecar)
- [FastAPI on App Service](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat/create)
- [Phi-3 Model on Hugging Face](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx)

---

## 📝 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- Microsoft Azure Samples Team
- FastAPI Community
- ONNX Runtime Team
- Hugging Face

---

**Built with ⚡ by Ultron — Azure AI Deployment Agent v1.0.0**
