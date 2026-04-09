import subprocess
import sys
import json

def run_ruff():
    """Run ruff for fast linting and style checking."""
    try:
        # Check if ruff is installed, if not try to install it or skip
        result = subprocess.run(
            ["ruff", "check", ".", "--format", "json"],
            capture_output=True, text=True
        )
        if result.stdout:
            return json.loads(result.stdout)
        return []
    except FileNotFoundError:
        return {"error": "ruff not found. Please install with 'pip install ruff'"}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("Running Elite Style Enforcer...")
    ruff_results = run_ruff()
    
    if isinstance(ruff_results, dict) and "error" in ruff_results:
        print(f"Error: {ruff_results['error']}")
        sys.exit(1)
        
    findings_count = len(ruff_results)
    print(json.dumps({
        "report_type": "Elite Style Audit",
        "findings_count": findings_count,
        "status": "PASS" if findings_count == 0 else "FAIL",
        "recommendation": "Run 'ruff check . --fix' to automatically resolve most issues."
    }, indent=2))

if __name__ == "__main__":
    main()
