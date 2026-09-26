# Receipt & Personal Finance Pipeline

An end-to-end personal-finance data platform: camera/upload receipt capture →
OCR + ML parsing → PostgreSQL → desktop GUI + REST API + LLM natural-language
query layer, with an edge deployment on a Raspberry Pi 4 "scanning station."

See [`docs/SRS.md`](docs/SRS.md) for full requirements and
[`docs/adr/`](docs/adr) for architecture decisions.

## Repo layout

```
db/                    SQLAlchemy models + Alembic migrations
src/ingestion/          validates and writes incoming receipt data
src/ml/training/        offline training pipeline (OCR post-processing model, classifier)
src/ml/inference/       shared inference code, used by both edge and API
src/edge/                Pi 4 capture + on-device inference service
src/api/                 FastAPI REST API
src/gui/                 PySide6 desktop app
src/llm/                 text-to-SQL natural-language query layer
src/common/              shared config, logging, schemas (pydantic)
tests/unit/              fast, no external dependencies
tests/integration/       hits a real (test) Postgres instance
tests/hardware/          smoke tests run on the Pi 4 itself, not in CI
scripts/                 one-off/dev scripts (seed data, model export, etc.)
data/                    raw/processed/models — gitignored except .gitkeep
```

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# start Postgres (adjust to your setup)
docker run --name receipts-db -e POSTGRES_PASSWORD=devpass -p 5432:5432 -d postgres:16

# apply migrations
alembic upgrade head

# run tests
pytest tests/unit tests/integration

# run the API
uvicorn src.api.main:app --reload
```

## Development workflow

- Trunk-based development: short-lived feature branches off `main`, PR per
  feature/fix, no direct pushes to `main`
- Conventional commits: `feat:`, `fix:`, `chore:`, `test:`, `docs:`, `refactor:`
- CI (`.github/workflows/ci.yml`) runs ruff, mypy, and pytest on every push
- Every non-trivial architectural decision gets a short ADR in `docs/adr/`
  (see `docs/adr/0001-record-architecture-decisions.md` for the template)

## Status

Scaffold only — see `docs/SRS.md` §7 for the build-order milestones.
