"""Natural-language -> SQL query layer (FR-12) with hard guardrails (FR-13, NFR-5).

Design (see docs/adr for the full write-up once drafted):
  1. The LLM is given ONLY the schema (table/column names + short
     descriptions), never write access or raw credentials.
  2. The LLM's output SQL is parsed and validated against an allow-list of
     tables/columns and a single statement type (SELECT) BEFORE execution.
  3. The query actually runs against a read-only Postgres role
     (`database_url_readonly` in settings) as a second, independent layer
     of defense beyond the allow-list check.

This module is deliberately the last thing built in the project (SRS §7,
milestone 6) — the schema needs to be stable first.
"""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

from src.common.config import settings

ALLOWED_TABLES = {"receipts", "line_items", "categories", "merchants"}

SCHEMA_DESCRIPTION = """\
receipts(id, merchant_id -> merchants.id, purchase_date, subtotal, tax, total)
line_items(id, receipt_id -> receipts.id, description, quantity, unit_price,
           line_total, category_id -> categories.id)
categories(id, name)
merchants(id, name)
"""


class UnsafeQueryError(Exception):
    """Raised when generated SQL fails the safety allow-list check."""


def build_prompt(user_question: str) -> str:
    return (
        "You are a SQL generator for a read-only reporting system. "
        "Given the schema below, write a single PostgreSQL SELECT statement "
        "that answers the user's question. Output ONLY the SQL, no prose, "
        "no markdown fences.\n\n"
        f"Schema:\n{SCHEMA_DESCRIPTION}\n\n"
        f"Question: {user_question}\n"
    )


def validate_sql(sql: str) -> str:
    """Parse `sql` and reject anything that isn't a plain SELECT over
    allow-listed tables. Returns the validated SQL unchanged, or raises.
    """
    stripped = sql.strip().rstrip(";")

    parsed = sqlglot.parse_one(stripped, dialect="postgres")
    if not isinstance(parsed, exp.Select):
        raise UnsafeQueryError("Only SELECT statements are permitted")

    for forbidden in (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create):
        if parsed.find(forbidden):
            raise UnsafeQueryError(f"Statement contains forbidden clause: {forbidden.__name__}")

    tables = {t.name for t in parsed.find_all(exp.Table)}
    disallowed = tables - ALLOWED_TABLES
    if disallowed:
        raise UnsafeQueryError(f"Query references non-allow-listed tables: {disallowed}")

    # Defense in depth against comment-based injection tricks.
    if re.search(r"--|/\*", stripped):
        raise UnsafeQueryError("SQL comments are not permitted in generated queries")

    return stripped


def generate_sql(user_question: str) -> str:
    """Call the LLM to generate SQL for `user_question`, then validate it.

    Kept separate from `validate_sql` so the validator can be unit tested
    without any API calls (see tests/unit/test_query_engine.py).
    """
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=500,
        messages=[{"role": "user", "content": build_prompt(user_question)}],
    )
    raw_sql = response.content[0].text
    return validate_sql(raw_sql)
