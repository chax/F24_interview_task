import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from db.database import get_session
from main import app


@pytest.fixture(name="engine")
def engine_fixture():
    # In-memory SQLite shared across connections so every Session opened
    # against it (e.g. one per request in the API tests) sees the same data.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    # Plain instantiation (no `with`) so the app's lifespan never runs and
    # never touches the real database.db file on disk.
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
