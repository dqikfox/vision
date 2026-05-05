import json
from pathlib import Path

from elite_brain import Brain


def _retarget_brain_paths(brain: Brain, tmp_path: Path) -> None:
    brain._store.path = tmp_path / "semantic.json"
    brain._episodes.path = tmp_path / "episodes.json"
    brain._tasks.path = tmp_path / "tasks.json"
    brain._procedures.path = tmp_path / "procedures.json"
    brain._evolution.path = tmp_path / "adaptations.json"
    brain._store._entries.clear()
    brain._episodes._episodes.clear()
    brain._tasks._tasks.clear()
    brain._procedures._entries.clear()
    brain._evolution._rules.clear()


async def test_brain_ingest_persists_task_and_procedure(tmp_path) -> None:
    brain = Brain()
    _retarget_brain_paths(brain, tmp_path)

    await brain.ingest(
        user_message="Improve local model memory retrieval",
        assistant_response="Done. Updated retrieval and verified it.",
        tools_used=["read_file", "write_file"],
        latency_ms=12.0,
        outcome="success",
    )
    brain.save()

    task_data = json.loads((tmp_path / "tasks.json").read_text(encoding="utf-8"))
    assert len(task_data) == 1
    assert task_data[0]["goal"] == "Improve local model memory retrieval"
    assert task_data[0]["status"] == "completed"
    assert task_data[0]["last_actions"] == ["read_file", "write_file"]

    proc_data = json.loads((tmp_path / "procedures.json").read_text(encoding="utf-8"))
    assert len(proc_data) == 1
    assert proc_data[0]["tools_used"] == ["read_file", "write_file"]
    assert proc_data[0]["successes"] == 1


async def test_brain_augment_system_includes_task_and_procedure_context(tmp_path) -> None:
    brain = Brain()
    _retarget_brain_paths(brain, tmp_path)

    brain.track_task(
        "Improve local model memory retrieval",
        status="active",
        success_criteria=["relevant memories recalled"],
        steps=["audit recall", "rerank retrieved memories"],
        actions=["read_file"],
    )
    brain._procedures.remember(
        "Improve local model memory retrieval",
        ["read_file", "write_file"],
        "Used file inspection and patching successfully.",
        "success",
    )

    prompt = await brain.augment_system("BASE", "Improve local model memory retrieval")
    assert "TASK STATE:" in prompt
    assert "PROCEDURAL RECALL" in prompt
    assert "tools=read_file,write_file" in prompt


async def test_brain_status_reports_task_and_procedure_snapshots(tmp_path) -> None:
    brain = Brain()
    _retarget_brain_paths(brain, tmp_path)

    brain.track_task("Audit memory", status="active", actions=["read_file"])
    brain._procedures.remember("Audit memory", ["read_file"], "Success.", "success")

    status = brain.status()
    assert status["active_tasks"] >= 1
    assert status["task_snapshot"][0]["goal"] == "Audit memory"
    assert status["procedure_snapshot"][0]["tools_used"] == ["read_file"]
