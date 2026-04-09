import os
import ast
import json
from pathlib import Path

def analyze_file(file_path):
    """Analyze a Python file for Copilot-unfriendly patterns using AST."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(content)
        
        findings = {
            "missing_type_hints": [],
            "missing_docstrings": [],
            "complex_functions": [],
            "score": 100
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for docstrings
                if not ast.get_docstring(node):
                    findings["missing_docstrings"].append(node.name)
                    findings["score"] -= 5
                
                # Check for type hints (returns)
                if not node.returns:
                    findings["missing_type_hints"].append(f"{node.name} (returns)")
                    findings["score"] -= 2
                
                # Check for type hints (args)
                for arg in node.args.args:
                    if arg.arg != "self" and not arg.annotation:
                        findings["missing_type_hints"].append(f"{node.name} (arg: {arg.arg})")
                        findings["score"] -= 1
                
                # Simple complexity check (total nodes in function)
                complexity = len(list(ast.walk(node)))
                if complexity > 150:
                    findings["complex_functions"].append(f"{node.name} (nodes: {complexity})")
                    findings["score"] -= 10
                    
        findings["score"] = max(0, findings["score"])
        return findings
    except Exception as e:
        return {"error": str(e)}

def main():
    report = {}
    for root, dirs, files in os.walk("."):
        # Skip noisy directories
        if any(d in root for d in [".git", "__pycache__", ".gemini", "node_modules", "venv", ".vscode"]):
            continue
        for file in files:
            if file.endswith(".py") and file != "copilot_audit.py":
                file_path = os.path.relpath(os.path.join(root, file), ".")
                report[file_path] = analyze_file(file_path)
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
