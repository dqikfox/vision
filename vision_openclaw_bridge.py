"""Vision ↔ OpenClaw bidirectional bridge.

Reads the OpenClaw Bearer token from ~/.openclaw/openclaw.json and exposes
async helpers for health-check, model listing, and event pushing.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Defaults ───────────────────────────────────────────────────────────────────
_DEFAULT_GATEWAY_URL = "http://localhost:18789"
_DEFAULT_VISION_URL = "http://localhost:8765"
_OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"


def _load_token() -> str | None:
    """Load the Bearer token from the local OpenClaw config file."""
    try:
        if _OPENCLAW_CONFIG_PATH.exists():
            data = json.loads(_OPENCLAW_CONFIG_PATH.read_text(encoding="utf-8"))
            return data.get("token") or data.get("api_key") or data.get("bearer_token")
    except Exception as exc:
        logger.warning("Could not load OpenClaw token: %s", exc)
    return None


class OpenClawBridge:
    """Async bridge between Vision and the OpenClaw gateway.

    Args:
        gateway_url: Base URL of the OpenClaw gateway (default: http://localhost:18789).
        vision_url: Base URL of the Vision backend (default: http://localhost:8765).
        token: Bearer token for OpenClaw API. Falls back to config file / OPENCLAW_TOKEN env var.
    """

    def __init__(
        self,
        gateway_url: str | None = None,
        vision_url: str | None = None,
        token: str | None = None,
    ) -> None:
        self.gateway_url = (gateway_url or os.environ.get("OPENCLAW_GATEWAY_URL") or _DEFAULT_GATEWAY_URL).rstrip("/")
        self.vision_url = (vision_url or os.environ.get("VISION_BASE_URL") or _DEFAULT_VISION_URL).rstrip("/")
        self._token: str | None = token or os.environ.get("OPENCLAW_TOKEN") or _load_token()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _get(self, path: str, timeout: float = 5.0) -> dict[str, Any]:
        """Perform an authenticated GET against the OpenClaw gateway."""
        url = f"{self.gateway_url}{path}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=self._auth_headers())
            response.raise_for_status()
            return response.json()

    async def _post(self, path: str, payload: dict[str, Any], timeout: float = 10.0) -> dict[str, Any]:
        """Perform an authenticated POST against the OpenClaw gateway."""
        url = f"{self.gateway_url}{path}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload, headers=self._auth_headers())
            response.raise_for_status()
            return response.json()

    # ── Public API ─────────────────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the OpenClaw gateway.

        Returns:
            A dict with at least ``{"status": "ok"|"error", ...}``.
        """
        try:
            data = await self._get("/v1/models")
            return {"status": "ok", "gateway_url": self.gateway_url, "models_available": True, "raw": data}
        except httpx.ConnectError:
            return {"status": "error", "reason": "gateway_unreachable", "gateway_url": self.gateway_url}
        except httpx.HTTPStatusError as exc:
            return {
                "status": "error",
                "reason": f"http_{exc.response.status_code}",
                "gateway_url": self.gateway_url,
            }
        except Exception as exc:
            logger.error("OpenClaw health_check failed: %s", exc)
            return {"status": "error", "reason": str(exc), "gateway_url": self.gateway_url}

    async def get_models(self) -> list[dict[str, Any]]:
        """Return the list of models registered in OpenClaw.

        Returns:
            A list of model objects (OpenAI-compatible format).
        """
        data = await self._get("/v1/models")
        return data.get("data", []) if isinstance(data, dict) else []

    async def push_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Push a Vision event into the OpenClaw event bus.

        Args:
            event_type: Identifier for the event (e.g. ``"vision.tool_executed"``).
            payload: Arbitrary JSON-serialisable data attached to the event.

        Returns:
            The gateway's JSON response, or an error dict on failure.
        """
        body: dict[str, Any] = {"type": event_type, "source": "vision", "payload": payload}
        try:
            return await self._post("/v1/events", body)
        except httpx.ConnectError:
            return {"status": "error", "reason": "gateway_unreachable"}
        except httpx.HTTPStatusError as exc:
            return {"status": "error", "reason": f"http_{exc.response.status_code}"}
        except Exception as exc:
            logger.error("OpenClaw push_event failed: %s", exc)
            return {"status": "error", "reason": str(exc)}

    async def vision_health(self) -> dict[str, Any]:
        """Check the health of the Vision backend (self-referential check).

        Returns:
            A dict with at least ``{"status": "ok"|"error", ...}``.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.vision_url}/api/health")
                response.raise_for_status()
                return {"status": "ok", "vision_url": self.vision_url, "raw": response.json()}
        except httpx.ConnectError:
            return {"status": "error", "reason": "vision_unreachable", "vision_url": self.vision_url}
        except Exception as exc:
            return {"status": "error", "reason": str(exc), "vision_url": self.vision_url}


# ── Module-level singleton (lazy) ──────────────────────────────────────────────
_bridge_instance: OpenClawBridge | None = None


def get_bridge() -> OpenClawBridge:
    """Return the module-level OpenClawBridge singleton (created on first call)."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = OpenClawBridge()
    return _bridge_instance
