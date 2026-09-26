import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base


@pytest.fixture()
def db_session() -> Session:
    """Real Postgres session for integration tests. Expects DATABASE_URL to
    point at a disposable test database (see .github/workflows/ci.yml and
    README for local Docker setup). Wraps each test in a transaction that's
    rolled back, so tests don't leak data into each other.
    """
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://postgres:devpass@localhost:5432/receipts_test"
    )
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
