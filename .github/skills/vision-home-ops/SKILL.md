---
name: vision-home-ops
description: 'Operate Vision as a home-ops assistant for single-user PC, network, security, backup, and automation tasks.'
argument-hint: 'Describe the environment task: PC maintenance, network troubleshooting, security hardening, backups, monitoring, or automation.'
user-invocable: true
---

# Vision Home Ops

Use this skill when the goal is to apply Vision and Copilot to **single-user home operations**, not just application development.

## Core Objective

Maintain, secure, optimize, and automate a single-user home PC and network environment so it runs reliably, safely, and efficiently with minimal manual intervention.

## Scope
1. **System administration**
   - OS and software upkeep
   - Performance monitoring
   - Startup/background task optimization
   - Crash and slowdown troubleshooting

2. **Home network management**
   - Router, Wi-Fi, DHCP, DNS, and local IP basics
   - Connectivity, latency, and interference troubleshooting
   - Secure local network practices

3. **Security and protection**
   - Firewall and endpoint protection checks
   - Update hygiene
   - Account hardening and suspicious-activity review

4. **Backup and data protection**
   - Automated backups
   - Restore points and recovery validation
   - File/storage organization

5. **Automation and efficiency**
   - PowerShell, Python, shell scripts
   - Scheduled tasks or cron-style maintenance
   - Repetitive workflow automation

6. **Monitoring and maintenance**
   - Temps, disk health, resource use, network usage
   - Routine cleanup and operational notes

## Procedure
1. Classify the task by domain: system, network, security, backup, automation, or monitoring.
2. Read the nearest authoritative docs and current repo instructions.
3. Prefer safe, repeatable automation and documentation over one-off fixes.
4. Keep credentials, local secrets, and private network details out of code and docs.
5. If the work changes the repo’s supported workflow, update docs in the same change.

## Useful Surfaces
- `.github/copilot-instructions.md`
- `DOCUMENTATION_INDEX.md`
- `README.md`
- `setup.md`
- `chat_events.log`
- local system tools such as PowerShell, Event Viewer, Task Scheduler, `ipconfig`, `ping`, `tracert`, `netstat`

## Completion Checks
- The home-ops workflow is safer, more documented, or more automated than before
- Changes are operationally clear and reusable
- Related docs and instructions stay aligned
