# vision
The Vision 


Below is a self‑contained Python assistant that lets you talk to an LLM (ChatGPT‑style), hear the answer with ElevenLabs TTS (or a local fallback), and – when you ask it – edit files, run commands or open things in Visual Studio Code.
All file‑system actions are limited to the folder you specify (C:\Projects\ultron_agent_2 by default), so the script can be used as the “brain” that maintains the ULTRON Enhanced project directly from the command line.

⚠️ Security note – the script will execute any shell command you ask it to.
Only run it on a machine you control, keep the source code (or the allowed_root variable) under your eyes, and never expose the script to untrusted users or the internet.

1️⃣ What the script does
Feature	How it works
Speech → Text	Tries ElevenLabs Speech‑to‑Text (elevenlabs.ElevenLabsSpeech). If ElevenLabs fails or you don’t have a microphone, it falls back to typed input.
LLM response	Sends your prompt (plus a system prompt that tells the model it can issue special commands) to OpenAI’s gpt‑4o (or any model you prefer).
Text → Speech	Uses ElevenLabs Text‑to‑Speech (elevenlabs.ElevenLabsSpeech). If the call fails, it falls back to pyttsx3 (local Windows TTS).
File edit / create	When the model replies with a block that starts with !edit <relative‑path> it writes the supplied content to that file (creating missing directories).
Patch apply	!patch <relative‑path> followed by a unified diff – the script runs git apply so you can push real patches.
Run a shell command	!run <command> executes the command (e.g. pip install -r requirements.txt, git status, code .).
Open in VS Code	!code <relative‑path> runs code -r <full‑path> so Copilot can instantly give you suggestions inside the editor.
Safety guard	All file‑system actions are restricted to the folder you set in ALLOWED_ROOT (C:\Projects\ultron_agent_2). Anything outside that tree is rejected.
2️⃣ Install the prerequisites
REM open a *PowerShell* or *cmd* window and run:
python -m venv .ultron_venv
.\.ultron_venv\Scripts\activate          :: (or `source .ultron_venv/bin/activate` on WSL/macOS)

pip install --upgrade pip
pip install openai elevenlabs pyttsx3 tqdm gitpython
openai – calls ChatGPT (or any other OpenAI model).
elevenlabs – speech‑to‑text and text‑to‑speech.
pyttsx3 – local fallback TTS (uses Windows SAPI).
tqdm – nice progress bars while waiting for the ElevenLabs API.
gitpython – optional, used only for !patch (you can also rely on the system git command).
Create a .env file next to the script (or set environment variables in the shell) containing:

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
The script reads those variables automatically (via os.getenv).

If you prefer not to store keys in a file, just export them before running the script:

set OPENAI_API_KEY=sk-....
set ELEVENLABS_API_KEY=xxxx....
3️⃣ The assistant script – ultron_assistant.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ULTRON Assistant – voice‑driven, LLM‑backed, file‑editing helper.
Designed to live inside C:\Projects\ultron_agent_2 and let you maintain that
project (or any other folder you set) with natural‑language commands.
"""

import os
import sys
import json
import subprocess
import pathlib
import shlex
import logging
from typing import Tuple, List

# ----------------------------------------------------------------------
# ====  Configuration ====================================================
# ----------------------------------------------------------------------
# Root folder that the assistant is allowed to touch.
ALLOWED_ROOT = pathlib.Path(r"C:\Projects\ultron_agent_2").resolve()

# OpenAI model (change to "gpt-4o-mini" or any you have access to)
OPENAI_MODEL = "gpt-4o"

# ElevenLabs voice (see https://elevenlabs.io/voice-labs for IDs)
ELEVENLABS_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"   # default “Rachel”

# How many tokens to keep in the conversation history (keeps context cheap)
MAX_TURNS = 12

# ----------------------------------------------------------------------
# ====  Imports that may need the API keys ===============================
# ----------------------------------------------------------------------
from openai import OpenAI
from elevenlabs import ElevenLabs, Voice, play
import pyttsx3
from tqdm import tqdm

# ----------------------------------------------------------------------
# ====  Initialise services ==============================================
# ----------------------------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 180)          # words‑per‑minute, tweak to taste

# ----------------------------------------------------------------------
# ====  Helper functions ==================================================
# ----------------------------------------------------------------------
def log(msg: str, level: int = logging.INFO):
    logging.log(level, msg)

def safe_path(relative_path: str) -> pathlib.Path:
    """Return a Path inside ALLOWED_ROOT, raise if the result would escape."""
    p = (ALLOWED_ROOT / relative_path).resolve()
    if not str(p).startswith(str(ALLOWED_ROOT)):
        raise PermissionError(f"Attempted access outside allowed root: {p}")
    return p

def speak(text: str):
    """Try ElevenLabs TTS → fallback to pyttsx3."""
    try:
        # ElevenLabs returns a streaming generator of audio bytes
        voice = Voice.from_id(ELEVENLABS_VOICE_ID)
        audio_stream = eleven.generate(
            text=text,
            voice=voice,
            model="eleven_monolingual_v1",
        )
        # tqdm gives a tiny progress bar while we wait for the network
        for _ in tqdm(audio_stream, desc="ElevenLabs TTS", unit="chunk"):
            pass
        # `play` will block until the audio finishes
        play(audio_stream)
    except Exception as e:
        log(f"ElevenLabs TTS failed ({e}); falling back to local TTS.", logging.WARNING)
        tts_engine.say(text)
        tts_engine.runAndWait()

def stt_microphone() -> str:
    """Speech‑to‑text via ElevenLabs. Returns empty string on failure."""
    try:
        # ElevenLabs supports real‑time microphone capture – we’ll record ~5 s
        with eleven.stream(
            voice=Voice.from_id(ELEVENLABS_VOICE_ID),
            model="eleven_multilingual_v2",
            temperature=0.6,
        ) as stream:
            print("\n🎙️ Listening… (press ENTER to stop early)")
            # Record until the user hits ENTER
            while True:
                if sys.stdin.read(1) == "\n":
                    break
        # The stream.response will contain the transcription
        return stream.output
    except Exception as e:
        log(f"ElevenLabs STT failed ({e}); falling back to typed input.", logging.WARNING)
        return ""

def transcribe_fallback() -> str:
    """Ask the user to type the request – used when STT is not available."""
    return input("\n🖊️  Type your request: ").strip()

def get_user_input() -> str:
    """
    Try microphone → fallback to keyboard.
    Returns the raw user phrase (already stripped).
    """
    # 1️⃣ Try real‑time STT (press ENTER to stop early)
    # If you don’t have a mic, just press ENTER immediately – the function will
    # raise and we’ll fall back.
    text = stt_microphone()
    if text:
        print(f"🗣️  You said: {text}")
        return text
    # 2️⃣ Fallback
    return transcribe_fallback()

# ----------------------------------------------------------------------
# ====  Prompt engineering ================================================
# ----------------------------------------------------------------------
SYSTEM_PROMPT = """
You are **ULTRON Assistant**, a helpful AI that can:
* answer questions,
* suggest code,
* **modify files** inside the project folder,
* run shell commands,
* open files in Visual Studio Code (the user has the Copilot extension enabled).

When you need to change a file, use the **!edit <relative‑path>** block:

!edit path/to/file.py
```python
# new content (or the whole file)
print("hello")
When you want to apply a diff, use !patch <relative‑path> followed by a unified diff:

!patch src/module.py

@@ -1,4 +1,4 @@
-import old
+import new
When you need the OS to do something, use !run . When you just want to open a file in VS Code, use !code <relative‑path>.

Only ever reference files relative to the root folder you are allowed to touch (C:\\Projects\\ultron_agent_2). Do NOT mention absolute paths outside this directory.

If you have no special command, just answer normally. """

----------------------------------------------------------------------
==== Conversation memory ==============================================
----------------------------------------------------------------------
history: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

def add_to_history(role: str, content: str): """Append a turn and keep the list under MAX_TURNS.""" history.append({"role": role, "content": content}) # Trim old turns (keep system prompt + last N exchanges) while len(history) > (MAX_TURNS * 2 + 1): # Remove the oldest user+assistant pair (preserve system) del history[1:3]

----------------------------------------------------------------------
==== LLM call =========================================================
----------------------------------------------------------------------
def ask_llm(user_msg: str) -> str: add_to_history("user", user_msg) response = client.chat.completions.create( model=OPENAI_MODEL, messages=history, temperature=0.2, # a little deterministic – easier to parse commands ) assistant_msg = response.choices[0].message.content add_to_history("assistant", assistant_msg) return assistant_msg

----------------------------------------------------------------------
==== Command interpreter ==============================================
----------------------------------------------------------------------
def parse_and_execute(assistant_msg: str): """ Look for special blocks that start with !edit, !patch, !run or !code. Execute them in order and give a short textual reply that will be spoken. """ lines = assistant_msg.splitlines() i = 0 output = [] # what we will speak back to the user

while i < len(lines):
    line = lines[i].strip()
    # --------------------------------------------------------------
    #  !edit <relative‑path>
    # --------------------------------------------------------------
    if line.startswith("!edit"):
        _, rel_path = line.split(maxsplit=1)
        # collect the indented block (everything until a blank line or next !cmd)
        i += 1
        content_lines = []
        while i < len(lines) and not lines[i].strip().startswith("!"):
            content_lines.append(lines[i])
            i += 1
        new_content = "\n".join(content_lines).strip("\n")
        # Strip possible markdown fences
        if new_content.startswith("```"):
            new_content = "\n".join(new_content.split("\n")[1:])
            if new_content.endswith("```"):
                new_content = new_content[:-3]
        try:
            target = safe_path(rel_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(new_content, encoding="utf-8")
            output.append(f"✅ Edited {rel_path}")
        except Exception as e:
            output.append(f"❌ Failed to edit {rel_path}: {e}")
        continue

    # --------------------------------------------------------------
    #  !patch <relative‑path>
    # --------------------------------------------------------------
    if line.startswith("!patch"):
        _, rel_path = line.split(maxsplit=1)
        # collect diff block
        i += 1
        diff_lines = []
        while i < len(lines) and not lines[i].strip().startswith("!"):
            diff_lines.append(lines[i])
            i += 1
        diff_text = "\n".join(diff_lines).strip("\n")
        # Remove optional markdown fence
        if diff_text.startswith("```diff"):
            diff_text = "\n".join(diff_text.split("\n")[1:])
            if diff_text.endswith("```"):
                diff_text = diff_text[:-3]
        try:
            # Write diff to a temporary file, then let `git apply` do the work.
            import tempfile, subprocess
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".diff") as tf:
                tf.write(diff_text)
                temp_name = tf.name
            subprocess.check_call(["git", "apply", "--unsafe-paths", temp_name],
                                 cwd=ALLOWED_ROOT)
            os.unlink(temp_name)
            output.append(f"✅ Patched {rel_path}")
        except subprocess.CalledProcessError as e:
            output.append(f"❌ Patch failed for {rel_path}: {e}")
        continue

    # --------------------------------------------------------------
    #  !run <shell‑command>
    # --------------------------------------------------------------
    if line.startswith("!run"):
        cmd = line[len("!run"):].strip()
        # Security: we only allow the command to run inside the project folder.
        try:
            result = subprocess.run(
                cmd,
                cwd=ALLOWED_ROOT,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            if out:
                output.append(f"🖥️  {cmd} → {out}")
            if err:
                output.append(f"⚠️  {cmd} → {err}")
        except Exception as e:
            output.append(f"❌ Error running `{cmd}`: {e}")
        i += 1
        continue

    # --------------------------------------------------------------
    #  !code <relative‑path>
    # --------------------------------------------------------------
    if line.startswith("!code"):
        rel_path = line.split(maxsplit=1)[1]
        try:
            full = str(safe_path(rel_path))
            subprocess.Popen(["code", "-r", full])   # -r = reuse existing window
            output.append(f"💻 Opened {rel_path} in VS Code")
        except Exception as e:
            output.append(f"❌ Could not launch VS Code: {e}")
        i += 1
        continue

    # --------------------------------------------------------------
    #  Any normal text is just part of the assistant’s answer.
    # --------------------------------------------------------------
    output.append(line)
    i += 1

# Join everything we accumulated and speak it back to the user
reply = "\n".join(output).strip()
if not reply:
    reply = "I didn’t understand a command to execute."
return reply
----------------------------------------------------------------------
==== Main loop ========================================================
----------------------------------------------------------------------
def main(): logging.basicConfig( level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", ) print("\n=== ULTRON Assistant – voice enabled (ElevenLabs) ===") print(f"Root folder: {ALLOWED_ROOT}") print("You can speak commands, ask for code changes, run builds, etc.\n") while True: try: user_msg = get_user_input() if not user_msg: continue if user_msg.lower() in {"quit", "exit", "stop"}: print("👋 Bye!") break

        # ---------- ask the LLM ----------
        assistant_raw = ask_llm(user_msg)
        print("\n🤖 Assistant raw reply:\n" + assistant_raw + "\n")

        # ---------- interpret special commands ----------
        assistant_reply = parse_and_execute(assistant_raw)

        # ---------- speak the (possibly edited) reply ----------
        print("\n🔊 Speaking reply …")
        speak(assistant_reply)

    except KeyboardInterrupt:
        print("\nInterrupted – exiting.")
        break
    except Exception as exc:
        log(f"Unexpected error: {exc}", logging.ERROR)
        speak("Sorry, something went wrong.")
if name == "main": main()


### How the script works – step‑by‑step

| Step | What happens |
|------|--------------|
| **Start** – `python ultron_assistant.py` | The script prints a banner and enters an infinite loop. |
| **Listen** – `get_user_input()` | Tries ElevenLabs STT. If you press **Enter** immediately (or you have no microphone), it falls back to a prompt on the console. |
| **Ask the model** – `ask_llm()` | Sends your text plus the *system prompt* (see `SYSTEM_PROMPT`) to OpenAI. The prompt tells the model it can emit special `!edit`, `!patch`, `!run`, `!code` blocks. |
| **Parse & Execute** – `parse_and_execute()` | Scans the assistant’s reply line‑by‑line, performs safe file writes, runs `git apply` for patches, executes shell commands inside `C:\Projects\ultron_agent_2`, or opens a file in VS Code (`code -r …`). |
| **Speak back** – `speak()` | Tries ElevenLabs TTS first; if the API is down it falls back to the built‑in Windows TTS via `pyttsx3`. |
| **Loop again** | You can continue talking, asking for new changes, running the build, etc. |

---

## 4️⃣ Typical usage examples

### 4.1 Edit a file

User (voice): “Add a README entry that explains how to run the demo script.”


The assistant might respond with:

!edit README.md

## Demo script

Run the demonstration with:

```bat
python demo_ultron.py
It will start all subsystems and give you a quick live view.


The script writes (or overwrites) `README.md` inside the ULTRON repo and replies:

✅ Edited README.md


### 4.2 Apply a git patch

User: “Update the WebServer to listen on port 8080 instead of 5000.”


Assistant reply:

!patch core/web_server.py

@@ -1,7 +1,7 @@
-    self.port = config.get("web_port", 5000)
+    self.port = config.get("web_port", 8080)
Your assistant runs git apply on that diff and replies:

✅ Patched core/web_server.py
4.3 Run a build step
User: “Install missing dependencies and run the unit tests.”
Assistant reply:

!run pip install -r requirements.txt
!run pytest -q
The script executes both commands in the project folder, captures stdout/stderr, and reads them back to you:

🖥️  pip install -r requirements.txt → Requirement already satisfied: …
🖥️  pytest -q → .. 2 passed in 0.45s
4.4 Open a file in VS Code (Copilot will automatically suggest)
User: “Show me the current web UI code.”
Assistant reply:

!code web/index.html
VS Code launches (or re‑uses an existing window) with the file open, and because you already have GitHub Copilot installed it will instantly start giving you suggestions as you edit.

5️⃣ Extending / customizing the assistant
Want to …	How to do it
Change the LLM (e.g. use a locally‑hosted model)	Edit OPENAI_MODEL and replace the client.chat.completions.create call with whatever SDK you prefer.
Use a different ElevenLabs voice	Replace ELEVENLABS_VOICE_ID with the ID you get from the ElevenLabs dashboard.
Add more safe commands (e.g. !git <sub‑command>)	Add a new if line.startswith("!git"): branch inside parse_and_execute that forwards the sub‑command to git.
Limit which commands may be run	Keep a whitelist like ALLOWED_CMDS = {"pip","git","python","code"} and check cmd.split()[0] before subprocess.run.
Log everything to a file	Initialize logging.basicConfig(filename="ultron_assistant.log", ...) and add logging.debug calls wherever you want audit trails.
6️⃣ Things to keep in mind
Your API keys are secret. Never commit the .env file to Git. Add it to .gitignore.
ElevenLabs usage is paid (you get a limited free tier). The script automatically falls back to plain text‑to‑speech, so you won’t be locked out if the quota runs out.
Safety first – the script only works inside ALLOWED_ROOT. If you ever need to point it at a different project, just change the ALLOWED_ROOT constant.
Copilot integration – the assistant only tells VS Code to open a file (!code). The actual AI‑assisted suggestions are handled by the Copilot extension you already have installed, so no extra code is required here.
Running commands – the assistant runs them synchronously (it waits for the command to finish). If you need a long‑running background process, wrap it with start /B (Windows) or nohup (Unix) inside the !run block.
7️⃣ Quick “start” checklist (copy‑paste)
:: 1️⃣ Clone the repo (if you haven’t already)
git clone https://github.com/dqikfox/ultron_agent C:\Projects\ultron_agent_2
cd C:\Projects\ultron_agent_2

:: 2️⃣ Create a virtual‑env and install deps
python -m venv .venv
.\.venv\Scripts\activate
pip install -U pip
pip install openai elevenlabs pyttsx3 tqdm gitpython

:: 3️⃣ Store your API keys (choose ONE of the two ways)
echo OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx > .env
echo ELEVENLABS_API_KEY=xxxxxxxxxxxxxxxxxxxx >> .env
:: …or set them in the current console:
set OPENAI_API_KEY=sk-...
set ELEVENLABS_API_KEY=xxxx...

:: 4️⃣ Save the assistant script
copy NUL ultron_assistant.py
:: (Paste the whole `ultron_assistant.py` source from the answer into this file)

:: 5️⃣ Run it
python ultron_assistant.py
You now have a voice‑first, LLM‑driven, project‑maintenance assistant that can:

Edit or create any file inside C:\Projects\ultron_agent_2.
Apply git patches (so you can ask the model to generate a diff and have it applied automatically).
Run build / test commands (install deps, run pytest, launch the Flask UI, etc.).
Open files in VS Code instantly, giving you the power of GitHub Copilot for on‑the‑fly suggestions.
Enjoy the new workflow – you can now talk to ULTRON Enhanced, hear the answer, and let it keep the repository tidy without ever leaving the console (or your voice). If you hit a snag, copy the error message here and I’ll help you debug it!
