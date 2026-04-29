---
name: vision-git-ops
description: 'Git workflow for Vision — commits, branches, PRs, history inspection, and release tagging.'
argument-hint: 'Describe the git task: commit, branch, PR, tag, or history query.'
user-invocable: true
---

# Vision Git Ops

## Commit convention
```
feat(tools): add wait_for_pixel polling tool
fix(voice): prevent barge-in echo loop after TTS
chore(deps): update elevenlabs to 2.42.0
docs(readme): update MCP server list
refactor(llm): extract _fast_completion helper
perf(ocr): use Resampling.LANCZOS for Pillow 10+
```

## Daily workflow
```powershell
# Check status
git -C c:\project\vision status

# Stage and commit
git -C c:\project\vision add -A
git -C c:\project\vision commit -m "feat(scope): description"

# Push
git -C c:\project\vision push
```

## Before committing — checklist
- [ ] `python test_tools.py` passes
- [ ] `python test_vision.py` passes  
- [ ] No secrets in diff (`git diff | Select-String "sk-|ghp_|AIza"`)
- [ ] `.env` not staged (`git status` should not show `.env`)
- [ ] `memory.json` and `chat_events.log` not staged

## Inspect history via MCP git server
The `git` MCP server is configured for `C:\project\vision`.
Use it to: list commits, show diffs, find when a bug was introduced.

## Never
- Force-push to main without explicit approval
- Commit `.env`, `memory.json`, `chat_events.log`, `.pw_profile/`
- Merge without at least one passing test run
