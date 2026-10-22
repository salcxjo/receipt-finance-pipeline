# Receipt & Personal Finance Pipeline

An end-to-end personal-finance data platform: receipt photos from an Android
phone → OCR + ML parsing → PostgreSQL → desktop GUI + REST API + LLM
natural-language query layer.

See [`docs/SRS.md`](docs/SRS.md) for full requirements and
[`docs/adr/`](docs/adr) for architecture decisions.

## Repo layout

```
db/                    SQLAlchemy models + Alembic migrations
src/ingestion/          validates and writes incoming receipt data
src/ml/training/        offline training pipeline (OCR post-processing model, classifier)
src/ml/inference/       shared inference code, used by both edge and API
src/api/                 FastAPI REST API
src/gui/                 PySide6 desktop app
src/llm/                 text-to-SQL natural-language query layer
src/common/              shared config, logging, schemas (pydantic)
tests/unit/              fast, no external dependencies
tests/integration/       hits a real (test) Postgres instance
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

## Uploading receipts from your phone

1. Set `UPLOAD_API_KEY` in `.env` (see `.env.example` for how to generate one).
2. Run the API so other devices can reach it: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
3. Put the phone and the server on the same private network. Easiest: install
   Tailscale on both (works from anywhere), or use the same Wi-Fi and allow
   port 8000 through the firewall.
4. On the phone open `http://<server-ip-or-tailscale-name>:8000/upload`, enter the
   API key once, and tap "Take photo". Use Chrome's "Add to Home screen" for a
   one-tap shortcut. Never expose this port to the public internet.

## Development workflow

- Trunk-based development: short-lived feature branches off `main`, PR per
  feature/fix, no direct pushes to `main`
- Conventional commits: `feat:`, `fix:`, `chore:`, `test:`, `docs:`, `refactor:`
- CI (`.github/workflows/ci.yml`) runs ruff, mypy, and pytest on every push
- Every non-trivial architectural decision gets a short ADR in `docs/adr/`
  (see `docs/adr/0001-record-architecture-decisions.md` for the template)

## Status

Scaffold only — see `docs/SRS.md` §7 for the build-order milestones.
