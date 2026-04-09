import os
import json
from pathlib import Path

def map_project():
    project_map = {
        "structure": {},
        "dependencies": {},
        "conventions": {
            "style": "PEP 8",
            "type_hints": "Required for Elite Status",
            "docstrings": "Google Style preferred"
        }
    }
    
    for root, dirs, files in os.walk("."):
        if any(d in root for d in [".git", "__pycache__", ".gemini", "node_modules", "venv", ".vscode"]):
            continue
        rel_root = os.path.relpath(root, ".")
        project_map["structure"][rel_root] = [f for f in files if f.endswith((".py", ".html", ".css", ".js"))]

    return project_map

def main():
    print("Mapping Elite Project Context...")
    context = map_project()
    
    with open("hive_tools/project_context.json", "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2)
        
    print("Project context mapped to hive_tools/project_context.json")

if __name__ == "__main__":
    main()
