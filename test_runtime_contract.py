from __future__ import annotations

import json

from vision_runtime import (
    AutomationState,
    CommandCenterConfig,
    HealthSnapshot,
    VoiceSettingsSnapshot,
    load_automation_state,
    load_command_center_config,
    merge_nested_dicts,
    save_automation_state,
    save_command_center_config,
)


def test_merge_nested_dicts_preserves_defaults() -> None:
    merged = merge_nested_dicts(
        {"theme": "vision", "launcher": {"host": "127.0.0.1", "mode": "local"}},
        {"launcher": {"mode": "lan"}, "profile_name": "prod"},
    )

    assert merged == {
        "theme": "vision",
        "launcher": {"host": "127.0.0.1", "mode": "lan"},
        "profile_name": "prod",
    }


def test_command_center_config_round_trip(tmp_path) -> None:
    config_path = tmp_path / "vision_command_center_config.json"

    initial = load_command_center_config(config_path)
    assert isinstance(initial, CommandCenterConfig)
    assert initial.launcher.ollama_host == "0.0.0.0:11434"

    saved = save_command_center_config(
        config_path,
        {
            "profile_name": "production",
            "launcher": {"ollama_access_mode": "local", "open_command_center": True},
        },
    )

    reloaded = load_command_center_config(config_path)
    assert saved.profile_name == "production"
    assert reloaded.launcher.ollama_access_mode == "local"
    assert reloaded.launcher.open_command_center is True
    assert reloaded.launcher.ollama_host == "0.0.0.0:11434"
    assert json.loads(config_path.read_text(encoding="utf-8"))["profile_name"] == "production"


def test_automation_state_normalizes_history(tmp_path) -> None:
    state_path = tmp_path / "vision_automation_state.json"
    state_path.write_text(
        json.dumps({"updated_at_utc": None, "routine_runs": "bad", "mission_runs": [{"id": "m1"}]}),
        encoding="utf-8",
    )

    state = load_automation_state(state_path)
    assert state.routine_runs == []
    assert state.mission_runs == [{"id": "m1"}]

    saved = save_automation_state(
        state_path,
        AutomationState(routine_runs=[{"id": "r1", "ok": True}], mission_runs=state.mission_runs),
    )
    assert saved.updated_at_utc is not None

    reloaded = load_automation_state(state_path)
    assert reloaded.routine_runs[0]["id"] == "r1"


def test_health_snapshot_serializes_nested_voice_settings() -> None:
    payload = HealthSnapshot(
        ollama=True,
        elevenlabs=False,
        ocr=True,
        gpu=False,
        browser=True,
        anthropic_sdk=False,
        brain={"status": "ok"},
        providers={"openai": True},
        high_contrast=False,
        keyboard_nav=True,
        voice_settings=VoiceSettingsSnapshot(
            preferred_stt="local",
            preferred_tts="elevenlabs",
            local_stt_available=True,
            elevenlabs_stt_available=True,
            groq_stt_available=False,
            rate=175,
            rate_min=100,
            rate_max=250,
            tts_voice_id="voice-123",
            pitch=50,
            pitch_min=25,
            pitch_max=75,
        ),
        voices=2,
    ).to_dict()

    assert payload["voice_settings"]["tts_voice_id"] == "voice-123"
    assert payload["providers"]["openai"] is True
