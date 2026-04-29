import json

from elite_brain import CritiqueResult, SelfEvolutionEngine


def _weak_critique(issue: str) -> CritiqueResult:
    return CritiqueResult(
        score=0.32,
        confidence=0.5,
        completeness=0.2,
        safety=0.95,
        issues=[issue],
        should_revise=True,
    )


async def test_self_evolution_engine_learns_rule_without_llm(tmp_path) -> None:
    engine = SelfEvolutionEngine(tmp_path / "adaptations.json")

    await engine.observe(
        user_message="How do I start the launcher on Windows?",
        assistant_response="Here is a long explanation but not the exact command.",
        critique=_weak_critique("The answer should lead with the exact command."),
        outcome="partial",
    )

    hits = engine.query("Need the exact Windows command to start it", top_k=1)
    assert len(hits) == 1
    assert "Lead with the exact command" in hits[0].guidance

    block = engine.build_guidance_block("Give me the Windows command")
    assert "SELF-EVOLUTION RULES" in block
    assert "exact command" in block


async def test_self_evolution_engine_persists_and_reinforces_success(tmp_path) -> None:
    path = tmp_path / "adaptations.json"
    engine = SelfEvolutionEngine(path)

    await engine.observe(
        user_message="My setup request is ambiguous.",
        assistant_response="I guessed instead of clarifying.",
        critique=_weak_critique("The request was ambiguous and needed clarification."),
        outcome="failure",
    )
    engine.save()

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert len(raw) == 1

    loaded = SelfEvolutionEngine(path)
    await loaded.observe(
        user_message="This setup request is ambiguous too.",
        assistant_response="I asked one focused question first.",
        critique=CritiqueResult(
            score=0.92,
            confidence=0.95,
            completeness=0.9,
            safety=0.9,
            issues=[],
            should_revise=False,
        ),
        outcome="success",
    )

    hits = loaded.query("This is another ambiguous setup request", top_k=1)
    assert len(hits) == 1
    assert hits[0].successes >= 1
