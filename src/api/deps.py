"""Shared FastAPI dependencies (DB session, etc.)."""

import secrets
from collections.abc import Generator

from fastapi import Header, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.common.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Gate for endpoints that accept data from outside (the phone upload).

    Fails closed: if UPLOAD_API_KEY isn't configured the endpoint is off,
    rather than silently open. compare_digest avoids timing leaks.
    """
    expected = settings.upload_api_key
    if not expected:
        raise HTTPException(status_code=503, detail="Uploads disabled: set UPLOAD_API_KEY")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
