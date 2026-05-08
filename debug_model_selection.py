import json
import urllib.request

def load_json(url: str, timeout: int = 10) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())

def main():
    BASE = "http://localhost:8765"
    payload = load_json(f"{BASE}/api/models")
    ollama_models_raw = payload.get("providers", {}).get("ollama", {}).get("models", [])
    ollama_models = ollama_models_raw if isinstance(ollama_models_raw, list) else str(ollama_models_raw).split()
    preferred_prefixes = ("gpt-oss", "llama3.2", "llama3.1", "qwen2.5", "qwen2")
    tool_model = next(
        (model for model in ollama_models if any(model.startswith(prefix) for prefix in preferred_prefixes)),
        "",
    )

    print("Available Ollama models:")
    for model in ollama_models:
        print(f"  {model}")

    print(f"\nPreferred prefixes: {preferred_prefixes}")
    print(f"Selected tool model: {tool_model}")

if __name__ == "__main__":
    main()
