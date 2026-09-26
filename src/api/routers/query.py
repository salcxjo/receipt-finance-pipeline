"""Natural-language query endpoint (FR-12). Runs generated SQL against a
read-only DB connection only — see src/llm/query_engine.py for guardrails.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.common.config import settings
from src.llm.query_engine import UnsafeQueryError, generate_sql

router = APIRouter()

_readonly_engine = (
    create_engine(settings.database_url_readonly) if settings.database_url_readonly else None
)


class NLQuery(BaseModel):
    question: str


@router.post("/")
def ask_question(payload: NLQuery, db: Session = Depends(get_db)) -> dict:
    try:
        sql = generate_sql(payload.question)
    except UnsafeQueryError as exc:
        raise HTTPException(status_code=422, detail=f"Rejected unsafe query: {exc}") from exc

    engine = _readonly_engine or db.get_bind()
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()

    return {"question": payload.question, "sql": sql, "rows": [dict(r) for r in rows]}
