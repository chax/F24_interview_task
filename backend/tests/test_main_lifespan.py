import asyncio

import main as main_module


def test_lifespan_calls_create_db_and_tables(monkeypatch):
    calls = []
    monkeypatch.setattr(main_module, "create_db_and_tables", lambda: calls.append(True))

    async def run():
        async with main_module.lifespan(main_module.app):
            pass

    asyncio.run(run())

    assert calls == [True]
