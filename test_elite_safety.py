import pytest
from elite_safety import AsyncSafety

def test_validate_proper_task_cleanup_leaks():
    code = """
async def do_work():
    task = asyncio.create_task(long_running_job())
    await do_other_things()
    """
    warnings = AsyncSafety.validate_proper_task_cleanup(code)
    assert "create_task used without visible cancel() — may leak tasks" in warnings

def test_validate_proper_task_cleanup_gather_exceptions():
    code = """
async def do_work():
    await asyncio.gather(task1(), task2())
    """
    warnings = AsyncSafety.validate_proper_task_cleanup(code)
    assert "gather() without return_exceptions may fail if one task raises" in warnings

def test_validate_proper_task_cleanup_safe():
    code = """
async def do_work():
    task = asyncio.create_task(long_running_job())
    try:
        await do_other_things()
    finally:
        task.cancel()

    await asyncio.gather(task1(), task2(), return_exceptions=True)
    """
    warnings = AsyncSafety.validate_proper_task_cleanup(code)
    assert len(warnings) == 0
