---
name: vision-multi-monitor
description: 'Handle multi-monitor setups in Vision operator. Use for targeting specific screens, capturing regions, clicking on secondary monitors, and managing window placement across displays.'
argument-hint: 'Describe the multi-monitor task: capture screen 2, click on secondary display, move window, or get monitor layout.'
user-invocable: true
---

# Vision Multi-Monitor

## Get Monitor Layout via run_command
```powershell
# PowerShell — list all monitors with resolution and position
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Screen]::AllScreens | Select-Object DeviceName, Bounds, Primary
```

## Coordinate System
- pyautogui uses the **virtual desktop** coordinate space
- Monitor 1 (primary): typically starts at (0, 0)
- Monitor 2 (right): starts at (primary_width, 0) e.g. (1920, 0)
- Monitor 2 (left): starts at (-1920, 0)
- Monitor 2 (above): starts at (0, -1080)

## Targeting Secondary Monitor

### Click on monitor 2
```python
# If monitor 2 starts at x=1920:
click(x=1920 + target_x, y=target_y)
```

### Screenshot of specific monitor region
```python
# Capture only monitor 2 (1920x1080 starting at x=1920)
screenshot_region(x=1920, y=0, width=1920, height=1080)
```

### Move window to monitor 2
```python
focus_window("Notepad")
# Then use run_command with PowerShell to move it:
run_command('powershell -c "Add-Type -A System.Windows.Forms; $w = [System.Windows.Forms.Form]; ..."')
```

## Common Patterns

### "What's on my second screen?"
```
1. run_command to get monitor bounds
2. screenshot_region(x=1920, y=0, width=1920, height=1080)
3. read_screen on that region
```

### "Click the button on the right monitor"
```
1. read_screen (full virtual desktop)
2. Identify coordinates (will be > 1920 for right monitor)
3. click(x, y) — pyautogui handles virtual desktop coords natively
```

## Notes
- `pyautogui.size()` returns the full virtual desktop size (all monitors combined)
- `pyautogui.screenshot()` captures ALL monitors by default
- For OCR accuracy on a specific monitor, always crop to that monitor's bounds first
