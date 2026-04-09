---
name: vision-adb-control
description: 'Control Android devices via ADB from within Vision. Use for mobile automation, screenshots, app launching, tap/swipe input injection, and WiFi ADB.'
argument-hint: 'Describe the Android task: launch app, tap coordinates, swipe, type text, screenshot, or install APK.'
user-invocable: true
---

# Vision ADB Control

## Prerequisites
ADB is installed at: `C:\Users\CHANN0$\AppData\Local\Android\Sdk\platform-tools\adb.exe`

Add to PATH permanently:
```powershell
[System.Environment]::SetEnvironmentVariable(
  "PATH",
  [System.Environment]::GetEnvironmentVariable("PATH","User") + ";C:\Users\CHANN0$\AppData\Local\Android\Sdk\platform-tools",
  "User"
)
```

Verify: `adb devices` — device must show as `device` (not `unauthorized`)

## Commands via run_command

```bash
adb devices                                          # list connected devices
adb shell screencap /sdcard/s.png && adb pull /sdcard/s.png C:\Users\CHANN0$\Desktop\phone.png
adb shell input tap 540 960                          # tap x y
adb shell input swipe 540 1500 540 500 300           # swipe x1 y1 x2 y2 ms
adb shell input text "hello"                         # type text
adb shell input keyevent 3                           # HOME
adb shell input keyevent 4                           # BACK
adb shell input keyevent 26                          # POWER
adb shell am start -n com.package/.MainActivity      # launch app
adb install C:\path\to\app.apk                       # install APK
adb connect 192.168.1.x:5555                         # WiFi ADB
adb tcpip 5555                                       # enable WiFi ADB (USB first)
```

## Vision Integration Pattern
```
"Take a screenshot of my phone"
→ run_command("adb shell screencap /sdcard/s.png && adb pull /sdcard/s.png C:\\Users\\CHANN0$\\Desktop\\phone.png")
→ screenshot shown in Vision UI
```

## Troubleshooting
| Issue | Fix |
|---|---|
| `adb: not recognized` | Add platform-tools to PATH (above) |
| `unauthorized` | Accept USB debugging prompt on device |
| `offline` | `adb kill-server && adb start-server` |
| WiFi not connecting | Enable via USB first: `adb tcpip 5555` |
