import asyncio

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import main as main_module
from db.model import File


@pytest.fixture(name="test_engine")
def test_engine_fixture(monkeypatch):
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(test_engine)
    monkeypatch.setattr(main_module, "engine", test_engine)
    yield test_engine
    test_engine.dispose()


def run_lifespan():
    async def run():
        async with main_module.lifespan(main_module.app):
            pass

    asyncio.run(run())


def test_lifespan_calls_create_db_and_tables(monkeypatch, test_engine):
    calls = []
    monkeypatch.setattr(main_module, "create_db_and_tables", lambda: calls.append(True))

    run_lifespan()

    assert calls == [True]


def test_lifespan_ensures_root_folder_exists(monkeypatch, test_engine):
    monkeypatch.setattr(main_module, "create_db_and_tables", lambda: None)

    run_lifespan()

    with Session(test_engine) as session:
        roots = session.exec(
            select(File).where(File.parent_id.is_(None))
        ).all()
    assert len(roots) == 1
    assert roots[0].name == "root"


def test_lifespan_does_not_duplicate_root_folder_on_repeated_startup(monkeypatch, test_engine):
    monkeypatch.setattr(main_module, "create_db_and_tables", lambda: None)

    run_lifespan()
    run_lifespan()

    with Session(test_engine) as session:
        roots = session.exec(
            select(File).where(File.parent_id.is_(None))
        ).all()
    assert len(roots) == 1
