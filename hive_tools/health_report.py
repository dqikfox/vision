import os
import sys
import psutil
import json
import platform
import subprocess
from pathlib import Path

def get_env_info():
    return {
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": psutil.cpu_count(),
        "memory_total": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
        "memory_available": f"{psutil.virtual_memory().available / (1024**3):.2f} GB",
        "disk_free": f"{psutil.disk_usage('.').free / (1024**3):.2f} GB",
    }

def check_keys():
    # Load .env file manually if python-dotenv isn't installed
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip()

    # Elite check: don't log the values, just presence
    keys = ["OPENAI_API_KEY", "GITHUB_TOKEN", "ELEVENLABS_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "GROQ_API_KEY"]
    status = {}
    for key in keys:
        status[key] = "SET" if os.environ.get(key) else "MISSING"
    return status

def check_dependencies():
    core_packages = [
        "fastapi", "uvicorn", "websockets", "sounddevice", "numpy", 
        "scipy", "pyautogui", "pytesseract", "elevenlabs", "openai"
    ]
    missing = []
    for pkg in core_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    return {
        "status": "HEALTHY" if not missing else "DEGRADED",
        "missing": missing
    }

def main():
    try:
        timestamp = subprocess.check_output(["powershell", "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"]).decode().strip()
    except:
        timestamp = "Unknown"

    report = {
        "report_type": "Elite Environment Health Index",
        "timestamp": timestamp,
        "env": get_env_info(),
        "keys": check_keys(),
        "dependencies": check_dependencies(),
    }
    
    # Calculate EHI (Environment Health Index)
    score = 100
    if report["dependencies"]["status"] == "DEGRADED":
        score -= 50
    missing_keys = [k for k, v in report["keys"].items() if v == "MISSING"]
    score -= len(missing_keys) * 10
    
    report["ehi_score"] = max(0, score)
    report["status"] = "ELITE" if report["ehi_score"] >= 90 else "DEGRADED"

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
