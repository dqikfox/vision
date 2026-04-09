import os
import re
import json
from pathlib import Path

def scan_for_secrets(file_path):
    secrets_patterns = [
        re.compile(r"sk-[a-zA-Z0-9]{32,}", re.IGNORECASE), # Generic sk- pattern
        re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE), # GitHub Token
        re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE), # Google API Key
    ]
    findings = []
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        for pattern in secrets_patterns:
            matches = pattern.findall(content)
            if matches:
                findings.append(f"Potential secret found in {file_path}")
    except Exception:
        pass
    return findings

def scan_unsafe_imports(file_path):
    unsafe = ["eval(", "exec(", "os.system("]
    findings = []
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        for u in unsafe:
            if u in content:
                findings.append(f"Unsafe use of {u} in {file_path}")
    except Exception:
        pass
    return findings

def main():
    findings = []
    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root or ".gemini" in root:
            continue
        for file in files:
            if file.endswith((".py", ".env", ".json", ".js", ".html")):
                file_path = os.path.join(root, file)
                findings.extend(scan_for_secrets(file_path))
                findings.extend(scan_unsafe_imports(file_path))
    
    report = {
        "report_type": "Elite Security Audit",
        "findings_count": len(findings),
        "findings": findings,
        "status": "SECURE" if not findings else "VULNERABLE"
    }
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
