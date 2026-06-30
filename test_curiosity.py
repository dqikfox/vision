import asyncio
from pathlib import Path
from elite_brain import CuriosityEngine, SemanticStore

async def main():
    store = SemanticStore(Path("test.json"))
    engine = CuriosityEngine(store)
    engine._queue.put_nowait("test")

    async def mock_llm(prompt, tokens):
        raise Exception("Mock error")

    engine.set_llm(mock_llm)

    task = asyncio.create_task(engine.run())
    await asyncio.sleep(0.1)
    print("Unfinished tasks:", engine._queue._unfinished_tasks)
    engine.stop()

asyncio.run(main())
