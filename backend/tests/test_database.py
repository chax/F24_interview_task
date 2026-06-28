from sqlalchemy import inspect
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, text

from db import database


def test_create_db_and_tables_creates_file_table(monkeypatch):
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    monkeypatch.setattr(database, "engine", test_engine)

    database.create_db_and_tables()

    assert inspect(test_engine).has_table("file")
    test_engine.dispose()


def test_get_session_yields_a_usable_session_and_closes_it(monkeypatch):
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    database.SQLModel.metadata.create_all(test_engine)
    monkeypatch.setattr(database, "engine", test_engine)

    session_gen = database.get_session()
    session = next(session_gen)
    assert isinstance(session, Session)
    assert session.exec(text("SELECT 1")).first() == (1,)

    # Advancing past the yield exits the `with Session(...)` block, closing it.
    next(session_gen, None)

    test_engine.dispose()
