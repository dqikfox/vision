from hive_tools.context_mapper import REPO_ROOT, build_context_brain


def test_build_context_brain_has_expected_sections() -> None:
    brain = build_context_brain(REPO_ROOT)

    assert brain["project"]["name"] == "vision"
    assert brain["entrypoints"]["backend"] == "live_chat_app.py"
    assert any(skill["name"] == "vision-context-ops" for skill in brain["catalog"]["skills"])
    assert any(agent["name"] == "Context Steward" for agent in brain["catalog"]["agents"])
    assert any(server["name"] == "vision-local" for server in brain["integration"]["mcp_servers"])
    assert any(
        workflow["name"] == "vision-repo-maintenance" for workflow in brain["automation"]["archon_workflows"]
    )
    assert brain["refresh"]["recommended_skill"] == "vision-context-brain"
    assert brain["refresh"]["recommended_council_skill"] == "vision-cognitive-council"
    assert brain["stats"]["skill_count"] >= 1
