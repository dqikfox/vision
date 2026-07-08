import json
import os
import sys
from pathlib import Path

# Resolve home folder dynamically (handles trailing $ if present in username)
home = Path.home()
config_path = home / ".gemini" / "config" / "mcp_config.json"

# Dynamically locate Python interpreter
python_candidates = [
    home / "AppData" / "Local" / "Python" / "pythoncore-3.14-64" / "python.exe",
    home / "AppData" / "Local" / "Programs" / "Python" / "Python313" / "python.exe",
    home / "AppData" / "Local" / "Programs" / "Python" / "Python312" / "python.exe",
    Path(sys.executable)
]
python_exe = next((str(p) for p in python_candidates if p.exists()), sys.executable)

# Resolve workspace path dynamically
workspace_path = str(Path(__file__).parent.resolve())

# Resolve extensions bundle path dynamically
extensions_dir = home / ".antigravity-ide" / "extensions"
bundle_path = None
if extensions_dir.exists():
    for child in extensions_dir.iterdir():
        if child.is_dir() and child.name.startswith("googlecloudtools.datacloud-"):
            candidate = child / "mcp_servers" / "cli" / "mcp_proxy_bundle.js"
            if candidate.exists():
                bundle_path = str(candidate)
                break

if not bundle_path:
    # Fallback to the standard path structure if not found dynamically
    bundle_path = str(extensions_dir / "googlecloudtools.datacloud-0.5.0-universal" / "mcp_servers" / "cli" / "mcp_proxy_bundle.js")

new_servers = {
    "vision-local": {
        "command": python_exe,
        "args": [
            str(Path(workspace_path) / "vision_mcp_server.py")
        ],
        "env": {
            "VISION_BASE_URL": "http://localhost:8765"
        }
    },
    "vision-admin": {
        "command": python_exe,
        "args": [
            str(Path(workspace_path) / "vision_admin_mcp.py")
        ]
    },
    "vision-rag-filesystem": {
        "command": python_exe,
        "args": [
            str(Path(workspace_path) / "launch_lmstudio_rag_mcp.py")
        ]
    },
    "vision-workspace-filesystem": {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-filesystem",
            workspace_path
        ]
    },
    "memory": {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-memory"
        ]
    },
    "sequential-thinking": {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-sequential-thinking"
        ]
    },
    "puppeteer": {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-puppeteer"
        ]
    },
    "brave-search": {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-brave-search"
        ],
        "env": {
            "BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY", "")
        }
    }
}

def main():
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {"mcpServers": {}}
        
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        removed_servers = []
        for deprecated_name in ("fetch", "git"):
            if deprecated_name in config["mcpServers"]:
                config["mcpServers"].pop(deprecated_name)
                removed_servers.append(deprecated_name)

        for deprecated_name in removed_servers:
            print(f"Removing deprecated MCP server: {deprecated_name}")
            
        for name, server_config in new_servers.items():
            config["mcpServers"][name] = server_config
            print(f"Adding/updating MCP server: {name}")
            
        # Ensure parent directories exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            
        print(f"Successfully updated MCP configuration at: {config_path}")
    except Exception as e:
        print(f"Error updating config: {e}")

if __name__ == "__main__":
    main()
