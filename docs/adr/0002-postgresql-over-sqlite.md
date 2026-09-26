# 2. Use PostgreSQL instead of SQLite

## Status
Accepted

## Context
Earlier edge projects (HomeEdge) used SQLite for simplicity. This project's
schema is more relational (receipts, line items, categories, merchants,
model versions, corrections) and the LLM query layer needs to generate and
run ad hoc SQL safely, which benefits from Postgres's stricter typing,
proper constraint enforcement, and role-based read-only access for the
LLM's query connection.

## Decision
Use PostgreSQL as the system of record, accessed via SQLAlchemy 2.0 ORM,
with Alembic managing all schema migrations. A separate read-only Postgres
role is created for the LLM query layer's connection (see ADR 0003, once
written, for the SQL guardrail design).

## Consequences
- Requires a running Postgres instance (Docker locally, real install on the
  Pi 4 or a small VM) instead of a single file — slightly more setup
- Gains: proper foreign keys/constraints, concurrent access from the API,
  GUI, and edge ingestion service simultaneously, and a natural place to
  enforce read-only access for LLM-generated queries
