import subprocess
import os

def run_cmd(args, cwd=None):
    res = subprocess.run(args, capture_output=True, text=True, shell=True, cwd=cwd)
    return res.stdout.strip(), res.stderr.strip()

workspace_dir = "c:/project/vision"
report_path = os.path.join(workspace_dir, "scratch/diff_report.txt")

# Make sure scratch directory exists
os.makedirs(os.path.dirname(report_path), exist_ok=True)

with open(report_path, "w", encoding="utf-8") as f:
    f.write("====================================================\n")
    f.write("          GIT BRANCHES & DIFF REPORT\n")
    f.write("====================================================\n\n")
    
    # 1. Current Branch
    branch, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workspace_dir)
    f.write(f"Active Branch: {branch}\n\n")
    
    # 2. Git Status
    status, _ = run_cmd(["git", "status"], cwd=workspace_dir)
    f.write("--- Git Status ---\n")
    f.write(status + "\n\n")
    
    # 3. List all local branches
    branches_raw, _ = run_cmd(["git", "branch"], cwd=workspace_dir)
    f.write("--- Local Branches ---\n")
    f.write(branches_raw + "\n\n")
    
    # 4. Diffs for each branch against HEAD
    branches = [b.strip().replace("* ", "") for b in branches_raw.split("\n") if b.strip()]
    for b in branches:
        if b == branch:
            continue
        f.write(f"--- Diff Stat for {b} vs {branch} ---\n")
        diff, err = run_cmd(["git", "diff", "--stat", f"{branch}..{b}"], cwd=workspace_dir)
        if diff:
            f.write(diff + "\n")
        else:
            f.write("No differences or error:\n" + (err if err else "No output") + "\n")
        f.write("\n")
        
    f.write("====================================================\n")

print(f"Report written to {report_path}")
