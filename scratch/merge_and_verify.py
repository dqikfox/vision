import subprocess
import os
import sys

def run_cmd(args, cwd=None):
    res = subprocess.run(args, capture_output=True, text=True, shell=True, cwd=cwd)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

workspace_dir = "c:/project/vision"
report_path = os.path.join(workspace_dir, "scratch/merge_report.txt")
test_path = os.path.join(workspace_dir, "scratch/test_results.txt")

os.makedirs(os.path.dirname(report_path), exist_ok=True)

# List of branches to merge
branches_to_merge = [
    "agents/voice-communication-enhancements",
    "copilot/set-local-voice-to-microsoft-ava"
]

with open(report_path, "w", encoding="utf-8") as f:
    f.write("====================================================\n")
    f.write("          AUTOMATIC MERGING & VERIFICATION\n")
    f.write("====================================================\n\n")

    # Check for dirty working tree first
    unstaged, _, _ = run_cmd(["git", "diff", "--name-only"], cwd=workspace_dir)
    staged, _, _ = run_cmd(["git", "diff", "--cached", "--name-only"], cwd=workspace_dir)
    
    if unstaged or staged:
        f.write("WARNING: Working tree is dirty. Committing temporary changes first...\n")
        # Stage everything and commit as a temp commit
        run_cmd(["git", "add", "-A"], cwd=workspace_dir)
        _, _, code = run_cmd(["git", "commit", "-m", "chore: temporary commit before merge"], cwd=workspace_dir)
        if code != 0:
            f.write("ERROR: Failed to commit uncommitted changes. Aborting.\n")
            sys.exit(1)
        f.write("Uncommitted changes saved to temporary commit.\n\n")
        
    for branch in branches_to_merge:
        f.write(f"--- Merging branch: {branch} ---\n")
        stdout, stderr, code = run_cmd(["git", "merge", branch], cwd=workspace_dir)
        f.write(f"Exit code: {code}\n")
        if stdout:
            f.write(f"STDOUT:\n{stdout}\n")
        if stderr:
            f.write(f"STDERR:\n{stderr}\n")
            
        if code != 0:
            f.write(f"CONFLICT / ERROR detected during merge of {branch}. Aborting this merge.\n")
            # Abort merge
            run_cmd(["git", "merge", "--abort"], cwd=workspace_dir)
        else:
            f.write(f"Successfully merged {branch}!\n")
        f.write("\n")

    f.write("====================================================\n")

print(f"Merge report written to {report_path}")

# Run tests
print("Running test suite...")
with open(test_path, "w", encoding="utf-8") as f:
    f.write("====================================================\n")
    f.write("               TEST SUITE EXECUTION\n")
    f.write("====================================================\n\n")
    
    for test_file in ["test_vision.py", "test_tools.py"]:
        f.write(f"--- Running {test_file} ---\n")
        stdout, stderr, code = run_cmd(["python", test_file], cwd=workspace_dir)
        f.write(f"Exit code: {code}\n")
        if stdout:
            f.write(f"STDOUT:\n{stdout}\n")
        if stderr:
            f.write(f"STDERR:\n{stderr}\n")
        f.write("\n")
        
    f.write("====================================================\n")

print(f"Test results written to {test_path}")
