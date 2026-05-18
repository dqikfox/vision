# 🎤 Voice Transcription Troubleshooting Guide

## Issue: Speech Not Being Transcribed

### **Quick Answer**
The voice overlay is **NOT required** for transcription. The web UI at `http://localhost:8765` should work on its own.

---

## 🔍 **Diagnostic Steps**

### **Step 1: Check Web UI is Open**
Open browser to: `http://localhost:8765`

### **Step 2: Check Mic Button State**

The microphone button (🎙) has **3 modes**:

1. **🚫 Muted** (red) - Voice capture disabled
2. **🎙 Standby** (white) - Click to capture one utterance
3. **🎙 Always-On** (green glow) - Continuous listening

**What to do**:
- If showing **🚫** → Click it to unmute
- If showing **🎙** (white) → Click it, then **speak immediately**
- If you want continuous listening → Enable "ALWAYS ON" mode

### **Step 3: Check Voice Mode Settings**

In the web UI, look for these toggles:

- **ALWAYS ON** - Continuous listening (recommended for hands-free)
- **WAKE** - Wake word detection ("hey vision")

**Recommended for hands-free use**:
```
ALWAYS ON: ✅ Enabled
WAKE: Your choice (optional)
```

### **Step 4: Test with Diagnostic Script**

Run this to see real-time voice activity:
```powershell
cd C:\project\vision
python test_voice_diagnostic.py
```

Then:
1. Click mic button in web UI
2. Speak clearly
3. Watch terminal for messages

You should see:
```
🔄 STATE: recording
🎤 VOLUME: ████ (0.15)
✅ TRANSCRIPT: your speech here
```

---

## 🐛 **Common Issues**

### **Issue 1: Mic button is 🚫 (muted)**
**Solution**: Click the microphone button once to unmute

### **Issue 2: Mic button is 🎙 (standby) but nothing happens**
**Problem**: Manual capture mode - you must click THEN speak quickly
**Solution**: 
- Enable "ALWAYS ON" mode for continuous listening
- OR click mic, then speak within 1-2 seconds

### **Issue 3: No audio input detected**
**Check**:
1. Browser permissions - Allow microphone access
2. System default mic - Check Windows Sound settings
3. Audio devices - Run diagnostic script to see volume bars

### **Issue 4: HTTPS/Secure Context Required**
Some browsers require HTTPS for microphone access.
**Solution**: 
- Use localhost (already HTTPS exempt)
- OR enable "Insecure origins treated as secure" in Chrome flags

### **Issue 5: Wrong STT Provider**
**Check**: Settings panel should show:
```
SPEECH-TO-TEXT: ElevenLabs ✅
```

If showing different provider or error:
1. Check ElevenLabs API key is set
2. Check `/api/health` shows `elevenlabs_stt_available: true`

---

## 🎯 **Quick Fixes**

### **Enable Continuous Listening** (Easiest)
1. Open web UI
2. Find "ALWAYS ON" toggle
3. Click to enable
4. Mic button should glow green
5. Just start talking - no button clicks needed!

### **Manual Capture Mode** (Click-to-Talk)
1. Click mic button
2. Speak within 1-2 seconds
3. Wait for transcription
4. Repeat for next utterance

---

## 🔧 **Backend Checks**

### **Verify Voice Loop is Running**
The backend should show:
```
[operator] Ready  ollama/cogito:latest - live_chat_app.py:5691
```

This means the voice loop started successfully.

### **Check Health Endpoint**
```powershell
curl http://localhost:8765/api/health | ConvertFrom-Json | Select voice_settings
```

Should show:
```json
{
  "preferred_stt": "elevenlabs",
  "preferred_tts": "elevenlabs",
  "local_stt_available": true,
  "elevenlabs_stt_available": true
}
```

---

## 🎤 **ElevenLabs API Key Check**

If ElevenLabs STT is not available:

1. **Check .env file** at `C:\project\vision\.env`:
   ```
   ELEVENLABS_API_KEY=your_key_here
   ```

2. **Verify in backend**: Look for `elevenlabs_stt_available: true` in health check

3. **Restart backend if needed**:
   ```powershell
   # Stop current backend (find PID)
   Get-Process -Id 11616 | Stop-Process

   # Start fresh
   cd C:\project\vision
   python live_chat_app.py
   ```

---

## 📊 **Expected Behavior**

### **Continuous Mode (ALWAYS ON)**
1. Enable "ALWAYS ON"
2. Mic glows green
3. Just talk - no clicking needed
4. Backend detects voice automatically
5. Transcription appears in chat
6. LLM responds

### **Manual Mode (Click-to-Talk)**
1. Click mic button (🎙)
2. Button changes color
3. Speak clearly (you have ~2 seconds)
4. VAD detects end of speech
5. Transcription appears
6. LLM responds

### **Wake Word Mode**
1. Enable "WAKE" toggle
2. Say "hey vision" or "ok vision"
3. Wait for acknowledgment
4. Speak your command
5. System processes

---

## 🆘 **Still Not Working?**

### **Run Full Diagnostic**
```powershell
cd C:\project\vision
python test_voice_diagnostic.py
```

### **Check Browser Console**
1. Press F12 in browser
2. Go to Console tab
3. Look for errors (especially microphone permission errors)

### **Check Backend Logs**
Look at terminal where `live_chat_app.py` is running for errors

### **Test with Overlay** (Alternative)
```powershell
cd C:\project\vision
python voice_overlay.py
```

The overlay has its own voice capture and might work if web UI doesn't.

---

## 💡 **Recommended Setup**

For best hands-free experience:

```
Web UI Settings:
- ALWAYS ON: ✅ Enabled
- WAKE: ❌ Disabled (unless you want wake word)
- Mic Button: Should glow green 🎙

Browser:
- Allow microphone access
- Use Chrome/Edge (best WebRTC support)
- localhost:8765 (no HTTPS issues)

Backend:
- ElevenLabs STT enabled
- Voice loop running
- No errors in logs
```

---

**Test Command**: "Hey, can you hear me?"

If you see the transcript appear in the chat → ✅ **Working!**

If nothing appears → Run `test_voice_diagnostic.py` and share output for further help.
