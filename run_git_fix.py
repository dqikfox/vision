import subprocess
import os
import sys

def run_cmd(args, cwd=None):
    res = subprocess.run(args, capture_output=True, text=True, shell=True, cwd=cwd)
    return res.stdout.strip(), res.stderr.strip()

print("=" * 60)
print("             GIT STATUS & BRANCH DIAGNOSTICS")
print("=" * 60)

# 1. Check current workspace status
workspace_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Workspace directory: {workspace_dir}")
branch, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workspace_dir)
print(f"Active branch in workspace: {branch}")

status, _ = run_cmd(["git", "status"], cwd=workspace_dir)
print("\n--- Workspace Git Status ---")
print(status if status else "(No output)")

# 2. Check worktrees
print("\n--- Git Worktrees ---")
wt_list, _ = run_cmd(["git", "worktree", "list"], cwd=workspace_dir)
print(wt_list if wt_list else "(No worktrees)")

# 3. Check for differences between voice enhancements branch and main
print("\n--- Branch Differences: agents/voice-communication-enhancements vs main ---")
diff_stat, _ = run_cmd(["git", "diff", "--stat", "main..agents/voice-communication-enhancements"], cwd=workspace_dir)
if diff_stat:
    print(diff_stat)
else:
    print("No differences found or branch does not exist locally.")

# 4. Check for conflicts or unmerged files
print("\n--- Unmerged / Conflicted Files ---")
conflicts, _ = run_cmd(["git", "diff", "--name-only", "--diff-filter=U"], cwd=workspace_dir)
if conflicts:
    print("WARNING: You have merge conflicts in these files:")
    print(conflicts)
else:
    print("No active merge conflicts detected in the main workspace.")

print("\n" + "=" * 60)
print("                     NEXT STEPS SUGGESTED")
print("=" * 60)
print("1. If you want to merge 'agents/voice-communication-enhancements' into 'main':")
print("   Run: python run_git_fix.py merge agents/voice-communication-enhancements")
print("2. If you want to clean up stale worktrees:")
print("   Run: python run_git_fix.py prune-worktrees")
print("=" * 60)

# Handle commands passed to the script
if len(sys.argv) > 1:
    action = sys.argv[1].lower()
    if action == "merge" and len(sys.argv) > 2:
        target_branch = sys.argv[2]
        print(f"\nAttempting to merge '{target_branch}' into '{branch}'...")
        # Check for uncommitted changes first
        unstaged, _ = run_cmd(["git", "diff", "--name-only"], cwd=workspace_dir)
        staged, _ = run_cmd(["git", "diff", "--cached", "--name-only"], cwd=workspace_dir)
        if unstaged or staged:
            print("ERROR: You have uncommitted changes. Please commit or stash them first.")
            sys.exit(1)
        
        stdout, stderr = run_cmd(["git", "merge", target_branch], cwd=workspace_dir)
        print("STDOUT:")
        print(stdout)
        if stderr:
            print("STDERR:")
            print(stderr)
    elif action == "prune-worktrees":
        print("\nPruning stale worktrees...")
        stdout, stderr = run_cmd(["git", "worktree", "prune"], cwd=workspace_dir)
        print(stdout if stdout else "Done.")
        if stderr:
            print("STDERR:", stderr)
