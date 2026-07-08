import os
import sys

keys_to_check = [
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "ELEVENLABS_API_KEY",
    "GROQ_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "XAI_API_KEY"
]

print("--- Environment Variables ---")
for key in keys_to_check:
    val = os.environ.get(key)
    if val:
        print(f"{key}: SET (length={len(val)}, starts with {val[:4]}...)")
    else:
        print(f"{key}: NOT SET")

# Also check for .env file
env_file_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_file_path):
    print(f"\n.env file exists at {env_file_path}")
    with open(env_file_path, "r", encoding="utf-8") as f:
        print("Lines in .env:")
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, _, _ = line.partition("=")
                print(f"  {k.strip()}: PRESENT")
else:
    print(f"\n.env file DOES NOT exist at {env_file_path}")
