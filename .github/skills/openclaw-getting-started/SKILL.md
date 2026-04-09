---
name: openclaw-getting-started
description: 'Install and bootstrap OpenClaw on Windows, WSL2, macOS, or Linux. Use for first-time setup, onboarding, gateway verification, dashboard launch, first chat validation, and basic troubleshooting.'
argument-hint: 'Describe your OS, preferred install path (installer/npm/source), and whether you need daemon auto-start.'
user-invocable: true
---

# OpenClaw Getting Started

Create a working OpenClaw setup in about 5 minutes with a repeatable install and verification flow.

## Documentation Index First
- Fetch the full docs index before deep-diving specific topics: `https://docs.openclaw.ai/llms.txt`
- Use that index to locate authoritative pages for install, onboarding, gateway, channels, tools, and troubleshooting.

## When to Use
- First-time OpenClaw setup
- Reinstalling OpenClaw after environment changes
- Setting up another machine with the same baseline
- Diagnosing why onboarding or gateway startup fails

## Inputs to Collect First
- OS: macOS, Linux, Windows native, or Windows with WSL2
- Node version (`node --version`), target: Node 24 recommended, Node 22.14+ supported
- Install method preference: installer script, package manager (`npm`), or source build
- Whether managed auto-start is required (`openclaw onboard --install-daemon` or `openclaw gateway install`)

## Decision Points
1. Platform choice on Windows:
- If user can use WSL2, use WSL2 path (recommended and most stable).
- If user must stay native Windows, use native path and mention caveats.

2. Install method:
- Fastest: installer script.
- Existing Node workflow: `npm install -g openclaw@latest`.
- Contributor/custom build needs: source install from repo.

3. Onboarding mode:
- QuickStart for defaults and fastest first chat.
- Advanced for explicit control of model/auth, gateway auth mode, channels, and daemon behavior.

## Procedure
1. Validate prerequisites.
- Run `node --version` and confirm supported version.
- For Windows users, prefer WSL2 when available.

2. Install OpenClaw.
- Recommended installer:
  - macOS/Linux/WSL2: `curl -fsSL https://openclaw.ai/install.sh | bash`
  - Windows PowerShell (native): `iwr -useb https://openclaw.ai/install.ps1 | iex`
- Package manager option:
  - `npm install -g openclaw@latest`
- Source option:
  - `git clone https://github.com/openclaw/openclaw.git`
  - `cd openclaw`
  - `pnpm install && pnpm ui:build && pnpm build`
  - `pnpm link --global`

3. Run onboarding.
- Standard: `openclaw onboard --install-daemon`
- If guided defaults are preferred, choose QuickStart.
- If explicit security/network/tooling choices are needed, choose Advanced.

4. Verify gateway health.
- `openclaw gateway status`
- Success criteria: gateway listens on port `18789`.

5. Open UI and validate chat.
- `openclaw dashboard`
- Send a simple message and confirm AI response.

6. Run post-setup checks.
- `openclaw --version`
- `openclaw doctor`
- Confirm onboarding completed and no critical health errors remain.

## Windows-Specific Branches
### WSL2 (preferred)
1. Install WSL and distro (PowerShell Admin):
- `wsl --install`
- Optional specific distro: `wsl --install -d Ubuntu-24.04`
2. Enable systemd in WSL:
- Add to `/etc/wsl.conf`:
  - `[boot]`
  - `systemd=true`
- Then run `wsl --shutdown` from PowerShell.
3. Re-open WSL terminal and continue with standard install + onboarding inside WSL.

### Native Windows (fallback)
1. Use install flow compatible with native CLI.
2. For managed startup:
- `openclaw gateway install`
- `openclaw gateway status --json`
3. If scheduled task creation is blocked, expect fallback to per-user Startup-folder login item.
4. For CLI-only without service install:
- `openclaw onboard --non-interactive --skip-health`
- `openclaw gateway run`

## Troubleshooting Branches
1. `openclaw` command not found.
- Check `node -v`.
- Check `npm prefix -g` and PATH.
- Ensure global npm bin path is in shell PATH.

2. Onboarding fails due to gateway health in non-interactive mode.
- Use `--skip-health` only when intentionally running without managed gateway.
- Re-run `openclaw doctor` and fix reported issues first.

3. Daemon install fails.
- On native Windows, verify scheduled task permissions.
- Re-run install with user-level fallback expectations.

## Completion Checklist
- OpenClaw CLI is installed and discoverable.
- Onboarding completed with provider/auth configured.
- Gateway status is healthy.
- Dashboard opens successfully.
- First chat round trip works.
- `openclaw doctor` has no blocking issues.

## References
- Documentation Index: https://docs.openclaw.ai/llms.txt
- Getting Started: https://docs.openclaw.ai/start/getting-started
- Install: https://docs.openclaw.ai/install
- Windows: https://docs.openclaw.ai/platforms/windows
- Onboarding (CLI): https://docs.openclaw.ai/start/wizard
- Gateway Configuration: https://docs.openclaw.ai/gateway/configuration
- Channels: https://docs.openclaw.ai/channels
- Tools and Plugins: https://docs.openclaw.ai/tools
- Environment Variables: https://docs.openclaw.ai/help/environment
