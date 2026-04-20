---
name: vision-type-safety
description: 'Fix mypy and Pylint type errors in Vision. Use when you see missing annotations, generic type params, or incompatible types.'
argument-hint: 'Describe the type error or paste the mypy output.'
user-invocable: true
---

# Vision Type Safety

## Run mypy
```powershell
python -m mypy c:\project\vision\live_chat_app.py --ignore-missing-imports --no-strict-optional 2>&1
```

## Common fixes in this codebase

### Missing generic params
```python
# ❌ mypy: Missing type parameters for generic type "dict"
history: list[dict] = []
data: dict = {}

# ✅
from typing import Any
history: list[dict[str, Any]] = []
data: dict[str, Any] = {}
```

### asyncio generics
```python
# ❌
audio_q: asyncio.Queue | None = None
speak_task: asyncio.Task | None = None

# ✅
audio_q: asyncio.Queue[np.ndarray] | None = None
speak_task: asyncio.Task[None] | None = None
```

### Missing return types
```python
# ❌
async def api_health():
    ...

# ✅
async def api_health() -> JSONResponse:
    ...
```

### Modules without stubs
```python
# scipy, pyttsx3, psutil — add type: ignore
from scipy.io import wavfile  # type: ignore[import-untyped]
import psutil  # type: ignore[import-untyped]
```

### Incompatible types to AsyncOpenAI
```python
# ❌ Sequence[str] not accepted
AsyncOpenAI(base_url=p["base_url"], api_key=key)

# ✅ explicit str cast
AsyncOpenAI(base_url=str(p["base_url"]), api_key=str(key))
```

### List[str | None] vs List[str]
```python
# ❌
return [m.model for m in resp.models]

# ✅ filter None
return [m.model for m in resp.models if m.model]
```
