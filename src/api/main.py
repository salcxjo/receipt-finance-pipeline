"""FastAPI application entrypoint (FR-11).

Routers are split by resource; this file only wires them together plus
shared middleware/DB session setup.
"""

from fastapi import FastAPI

from src.api.routers import categories, query, receipts

app = FastAPI(
    title="Receipt & Finance Pipeline API",
    version="0.1.0",
    description="REST API over the receipt/finance database.",
)

app.include_router(receipts.router, prefix="/receipts", tags=["receipts"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(query.router, prefix="/query", tags=["natural-language query"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
