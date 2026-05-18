from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

JsonDict = dict[str, Any]


def merge_nested_dicts(base: Mapping[str, Any], override: Mapping[str, Any]) -> JsonDict:
    """Merge nested mappings while preserving defaults for missing keys."""
    merged: JsonDict = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = merge_nested_dicts(current, value)
        else:
            merged[key] = value
    return merged


def _json_object(path: Path, error_message: str) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(error_message)
    return dict(payload)


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _as_optional_dict(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return dict(value)


@dataclass(slots=True)
class LauncherConfig:
    open_primary_ui: bool = True
    open_command_center: bool = False
    prefer_app_window: bool = True
    ollama_access_mode: str = "lan"
    ollama_host: str = "0.0.0.0:11434"
    ollama_origins: str = "http://localhost:8765,http://127.0.0.1:8765"
    ollama_models_path: str = r"F:\models"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> LauncherConfig:
        data = dict(payload) if isinstance(payload, Mapping) else {}
        return cls(
            open_primary_ui=bool(data.get("open_primary_ui", True)),
            open_command_center=bool(data.get("open_command_center", False)),
            prefer_app_window=bool(data.get("prefer_app_window", True)),
            ollama_access_mode=str(data.get("ollama_access_mode", "lan")),
            ollama_host=str(data.get("ollama_host", "0.0.0.0:11434")),
            ollama_origins=str(data.get("ollama_origins", "http://localhost:8765,http://127.0.0.1:8765")),
            ollama_models_path=str(data.get("ollama_models_path", r"F:\models")),
        )

    def to_dict(self) -> JsonDict:
        return asdict(self)


@dataclass(slots=True)
class DoctorConfig:
    check_context_brain: bool = True
    check_launchers: bool = True
    show_provider_keys: bool = True

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> DoctorConfig:
        data = dict(payload) if isinstance(payload, Mapping) else {}
        return cls(
            check_context_brain=bool(data.get("check_context_brain", True)),
            check_launchers=bool(data.get("check_launchers", True)),
            show_provider_keys=bool(data.get("show_provider_keys", True)),
        )

    def to_dict(self) -> JsonDict:
        return asdict(self)


@dataclass(slots=True)
class CommandCenterConfig:
    profile_name: str = "default"
    theme: str = "vision"
    auto_refresh_seconds: int = 30
    show_external_resources: bool = True
    launcher: LauncherConfig = field(default_factory=LauncherConfig)
    doctor: DoctorConfig = field(default_factory=DoctorConfig)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> CommandCenterConfig:
        data = dict(payload)
        return cls(
            profile_name=str(data.get("profile_name", "default")),
            theme=str(data.get("theme", "vision")),
            auto_refresh_seconds=_as_int(data.get("auto_refresh_seconds", 30), 30),
            show_external_resources=bool(data.get("show_external_resources", True)),
            launcher=LauncherConfig.from_mapping(data.get("launcher")),
            doctor=DoctorConfig.from_mapping(data.get("doctor")),
        )

    def to_dict(self) -> JsonDict:
        return {
            "profile_name": self.profile_name,
            "theme": self.theme,
            "auto_refresh_seconds": self.auto_refresh_seconds,
            "show_external_resources": self.show_external_resources,
            "launcher": self.launcher.to_dict(),
            "doctor": self.doctor.to_dict(),
        }


@dataclass(slots=True)
class AutomationState:
    updated_at_utc: str | None = None
    routine_runs: list[dict[str, Any]] = field(default_factory=list)
    mission_runs: list[dict[str, Any]] = field(default_factory=list)
    active_run: dict[str, Any] | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> AutomationState:
        data = dict(payload)
        return cls(
            updated_at_utc=_as_optional_str(data.get("updated_at_utc")),
            routine_runs=_as_dict_list(data.get("routine_runs")),
            mission_runs=_as_dict_list(data.get("mission_runs")),
            active_run=_as_optional_dict(data.get("active_run")),
        )

    def to_dict(self) -> JsonDict:
        return {
            "updated_at_utc": self.updated_at_utc,
            "routine_runs": list(self.routine_runs),
            "mission_runs": list(self.mission_runs),
            "active_run": dict(self.active_run) if isinstance(self.active_run, dict) else None,
        }


def begin_automation_run(
    state: AutomationState,
    *,
    kind: str,
    target_id: str,
    name: str,
    summary: str = "",
    total_steps: int = 1,
) -> dict[str, Any]:
    """Create and persist a normalized active automation run record."""
    now = datetime.now().isoformat()
    run = {
        "run_id": uuid4().hex,
        "kind": str(kind),
        "target_id": str(target_id),
        "name": str(name),
        "summary": str(summary),
        "status": "running",
        "started_at_utc": now,
        "updated_at_utc": now,
        "total_steps": max(1, int(total_steps)),
        "completed_steps": 0,
        "current_step": None,
    }
    state.active_run = run
    return run


def update_automation_run(state: AutomationState, **updates: Any) -> dict[str, Any]:
    """Mutate the current active automation run and normalize bookkeeping fields."""
    if not isinstance(state.active_run, dict):
        raise ValueError("No active automation run to update.")
    run = dict(state.active_run)
    run.update(updates)
    if "total_steps" in run:
        run["total_steps"] = max(1, _as_int(run.get("total_steps"), 1))
    if "completed_steps" in run:
        run["completed_steps"] = max(0, _as_int(run.get("completed_steps"), 0))
    run["updated_at_utc"] = datetime.now().isoformat()
    if not isinstance(run.get("current_step"), Mapping):
        run["current_step"] = None if run.get("current_step") is None else dict(run.get("current_step", {}))
    state.active_run = run
    return run


def finish_automation_run(
    state: AutomationState,
    *,
    kind: str,
    history_entry: Mapping[str, Any],
    limit: int = 20,
) -> dict[str, Any]:
    """Store a completed automation run in history and clear the active run slot."""
    key = "mission_runs" if kind == "mission" else "routine_runs"
    entry = dict(history_entry)
    history = [entry, *getattr(state, key)]
    setattr(state, key, history[: max(1, int(limit))])
    state.active_run = None
    return entry


@dataclass(slots=True)
class MetricsSnapshot:
    cpu: float | None = None
    ram: float | None = None
    ram_used_gb: float | None = None
    ram_total_gb: float | None = None
    disk: float | None = None
    disk_used_gb: float | None = None
    disk_total_gb: float | None = None
    gpu: float | None = None
    gpu_mem: float | None = None
    gpu_mem_gb: float | None = None
    gpu_total_gb: float | None = None
    gpu_name: Any = None

    def to_dict(self) -> JsonDict:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(slots=True)
class VoiceSettingsSnapshot:
    preferred_stt: str
    preferred_tts: str
    local_stt_available: bool
    elevenlabs_stt_available: bool
    groq_stt_available: bool
    rate: int
    rate_min: int
    rate_max: int
    tts_voice_id: str
    pitch: int
    pitch_min: int
    pitch_max: int

    def to_dict(self) -> JsonDict:
        return asdict(self)


@dataclass(slots=True)
class HealthSnapshot:
    ollama: bool
    elevenlabs: bool
    ocr: bool
    gpu: bool
    browser: bool
    anthropic_sdk: bool
    brain: dict[str, Any]
    providers: dict[str, bool]
    high_contrast: bool
    keyboard_nav: bool
    voice_settings: VoiceSettingsSnapshot
    voices: int

    def to_dict(self) -> JsonDict:
        payload = asdict(self)
        payload["voice_settings"] = self.voice_settings.to_dict()
        return payload


def load_command_center_config(path: Path) -> CommandCenterConfig:
    """Load the non-sensitive command center profile."""
    if not path.exists():
        config = CommandCenterConfig()
        save_command_center_config(path, config)
        return config
    return CommandCenterConfig.from_mapping(
        _json_object(path, "vision_command_center_config.json must contain a JSON object.")
    )


def save_command_center_config(path: Path, config: CommandCenterConfig | Mapping[str, Any]) -> CommandCenterConfig:
    """Persist the non-sensitive command center profile."""
    normalized = config if isinstance(config, CommandCenterConfig) else CommandCenterConfig.from_mapping(config)
    path.write_text(json.dumps(normalized.to_dict(), indent=2) + "\n", encoding="utf-8")
    return normalized


def load_automation_state(path: Path) -> AutomationState:
    """Load automation routine and mission history."""
    if not path.exists():
        state = AutomationState()
        save_automation_state(path, state)
        return state
    return AutomationState.from_mapping(
        _json_object(path, "vision_automation_state.json must contain a JSON object.")
    )


def save_automation_state(path: Path, state: AutomationState | Mapping[str, Any]) -> AutomationState:
    """Persist automation routine and mission history."""
    normalized = state if isinstance(state, AutomationState) else AutomationState.from_mapping(state)
    normalized.updated_at_utc = datetime.now().isoformat()
    path.write_text(json.dumps(normalized.to_dict(), indent=2) + "\n", encoding="utf-8")
    return normalized
