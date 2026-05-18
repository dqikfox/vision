# 3D Avatar Integration - Testing Checklist

## Backend Status
- ✅ Backend running on http://localhost:8765
- ✅ Health endpoint responding (200 OK)

## Browser Windows Opened

### 1. Diagnostic Page
**URL**: http://localhost:8765/diagnostic.html
**Purpose**: Automated checks of all components
**What to check**: Look for green ✓ or red ✗ next to each test

Expected results:
- ✓ THREE loaded
- ✓ GLTFLoader loaded  
- ✓ THREE_LOADED flag
- ✓ Canvas element
- ✓ init3DAvatar function
- ✓ Three.js import
- ✓ ensureBootServices call
- ✓ GLB fetch OK

### 2. Test Page
**URL**: http://localhost:8765/simple_3d_test.html
**Purpose**: Isolated 3D model test
**What to check**: 
- Should see Ultron character centered and rotating
- Top-left status text should say "Model loaded! Original: X.Xm, scaled to: 3.0m"
- No errors in console (F12)

### 3. Main UI
**URL**: http://localhost:8765
**Purpose**: Full Vision interface
**What to check**:
1. Boot screen appears
2. Click "CLICK TO ENTER"
3. Center of screen should show 3D Ultron avatar
4. Avatar should rotate and animate
5. Console (F12) should show:
   - "Three.js and GLTFLoader loaded successfully"
   - "3D Avatar script loaded"
   - "Initializing 3D Avatar..."
   - "Canvas and container found, proceeding..."
   - "Creating GLTFLoader..."
   - "Loading model from /assets/ultron-avatar.glb..."
   - "Model load success callback triggered"
   - "3D Ultron avatar loaded successfully"

## Manual Verification Steps

For each browser window:
1. Press F12 to open Developer Tools
2. Click "Console" tab
3. Look for errors (red text)
4. Copy any errors you see

## Report Format

Please provide:
1. **Diagnostic page**: List what shows ✓ and what shows ✗
2. **Test page**: Does Ultron model appear? Any console errors?
3. **Main UI**: Does avatar appear in center? Any console errors?

Example:
```
Diagnostic: All ✓ except GLTFLoader (shows ✗)
Test page: Model appears but too small
Main UI: No avatar, console shows "GLTFLoader is not defined"
```

## Files to Check if Issues Persist

If avatar still doesn't appear:
- `C:\project\vision\assets\ultron-avatar.glb` - Should be 4,952,140 bytes
- Browser cache - Try Ctrl+Shift+R to hard refresh
- Browser console - Look for CORS, network, or JavaScript errors

## Quick Fixes

**If GLB won't load**: 
```powershell
Copy-Item "F:\ultron_agent\Avatar\ultron+xps5.glb" "C:\project\vision\assets\ultron-avatar.glb" -Force
```

**If Three.js won't load**:
- Check internet connection (CDN dependency)
- Try different browser (Chrome/Edge)

**If nothing shows**:
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Check console for errors
