# Vercel entrypoint — re-exports the FastAPI `app` from live_chat_app.
# Vercel's FastAPI runtime discovers the `app` object from this file.
from live_chat_app import app

__all__ = ["app"]
