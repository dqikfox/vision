import asyncio
from pathlib import Path

from elite_brain import CuriosityEngine, SemanticStore


async def test_curiosity_engine_task_done_on_error(tmp_path: Path) -> None:
    """Ensure CuriosityEngine calls task_done even if the LLM function raises an error."""
    store = SemanticStore(tmp_path / "semantic.json")
    engine = CuriosityEngine(store)

    # Pre-populate the queue with a topic
    engine._queue.put_nowait("test error topic")

    # Create an LLM function that unconditionally raises an error
    async def mock_llm_error(prompt: str, max_tokens: int) -> str:
        raise Exception("Mock error for testing")

    engine.set_llm(mock_llm_error)

    # Start the engine's background task
    task = asyncio.create_task(engine.run())

    # Wait for the queue to be fully processed.
    # If task_done is not called, this will block forever.
    # Using a timeout to ensure the test fails if it blocks.
    try:
        await asyncio.wait_for(engine._queue.join(), timeout=1.0)
    except TimeoutError:
        task.cancel()
        assert False, "Queue join timed out, task_done() was likely not called."

    engine.stop()
    task.cancel()


async def test_curiosity_engine_task_done_when_no_llm(tmp_path: Path) -> None:
    """Ensure CuriosityEngine calls task_done even if no LLM is configured."""
    store = SemanticStore(tmp_path / "semantic.json")
    engine = CuriosityEngine(store)

    # No LLM is set initially
    assert engine._llm_fn is None

    engine._queue.put_nowait("test no llm topic")

    task = asyncio.create_task(engine.run())

    try:
        await asyncio.wait_for(engine._queue.join(), timeout=1.0)
    except TimeoutError:
        task.cancel()
        assert False, "Queue join timed out when no LLM was set."

    engine.stop()
    task.cancel()
