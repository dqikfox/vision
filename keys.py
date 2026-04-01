"""
keys.py — Secure API key loader
================================
Priority order:
  1. Environment variable (set externally / by .bat)
  2. Windows Credential Manager (most secure, never on disk as plain text)
  3. .env file in same directory (fallback)

Usage:
  from keys import get_key
  api_key = get_key("ELEVENLABS_API_KEY")
"""

import os
from pathlib import Path


def get_key(name: str, default: str = "") -> str:
    # 1. Environment variable
    val = os.environ.get(name, "").strip()
    if val:
        return val

    # 2. Windows Credential Manager
    try:
        import keyring
        val = keyring.get_password("operator", name) or ""
        if val:
            return val.strip()
    except Exception:
        pass

    # 3. .env file
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == name and v.strip():
                return v.strip()

    return default


def store_key(name: str, value: str) -> None:
    """Store a key in Windows Credential Manager."""
    try:
        import keyring
        keyring.set_password("operator", name, value)
        print(f"[keys] Stored {name} in Windows Credential Manager")
    except Exception as e:
        print(f"[keys] Could not store in Credential Manager: {e}")
        # Fall back: write to .env
        env_path = Path(__file__).parent / ".env"
        lines = []
        updated = False
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith(name + "=") or line.startswith(name + " ="):
                    lines.append(f"{name}={value}")
                    updated = True
                else:
                    lines.append(line)
        if not updated:
            lines.append(f"{name}={value}")
        env_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"[keys] Stored {name} in .env")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "set":
        store_key(sys.argv[2], input(f"Value for {sys.argv[2]}: ").strip())
    elif len(sys.argv) == 2:
        print(get_key(sys.argv[1]) or "(not set)")
    else:
        print("Usage: python keys.py <KEY_NAME>")
        print("       python keys.py set <KEY_NAME>")
