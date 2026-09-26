"""Receipt endpoints: list, get, and category spending summary (FR-10, FR-11)."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from pydantic import BaseModel

from db.models import Category, LineItem, Receipt
from src.api.deps import get_db
from src.common.schemas import ParsedReceipt
from src.ingestion.service import IngestionError, ingest_parsed_receipt

router = APIRouter()


class IngestRequest(BaseModel):
    parsed: ParsedReceipt
    image_path: str


@router.post("/ingest", status_code=201)
def ingest_receipt(payload: IngestRequest, db: Session = Depends(get_db)) -> dict:
    """Called by the edge scanning station after local OCR/parsing (FR-6)."""
    try:
        receipt = ingest_parsed_receipt(db, payload.parsed, payload.image_path)
    except IngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": str(receipt.id)}


@router.get("/")
def list_receipts(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 50,
) -> list[dict]:
    q = db.query(Receipt)
    if start_date:
        q = q.filter(Receipt.purchase_date >= start_date)
    if end_date:
        q = q.filter(Receipt.purchase_date <= end_date)
    receipts = q.order_by(Receipt.purchase_date.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "merchant": r.merchant.name if r.merchant else None,
            "purchase_date": r.purchase_date,
            "total": float(r.total) if r.total is not None else None,
        }
        for r in receipts
    ]


@router.get("/{receipt_id}")
def get_receipt(receipt_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    receipt = db.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return {
        "id": str(receipt.id),
        "merchant": receipt.merchant.name if receipt.merchant else None,
        "purchase_date": receipt.purchase_date,
        "total": float(receipt.total) if receipt.total is not None else None,
        "image_path": receipt.image_path,
        "line_items": [
            {
                "description": li.description,
                "quantity": float(li.quantity),
                "line_total": float(li.line_total),
                "category": li.category.name if li.category else None,
            }
            for li in receipt.line_items
        ],
    }


@router.get("/summary/by-category")
def summary_by_category(
    db: Session = Depends(get_db),
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    q = (
        db.query(Category.name, func.sum(LineItem.line_total).label("total"))
        .join(LineItem, LineItem.category_id == Category.id)
        .join(Receipt, Receipt.id == LineItem.receipt_id)
    )
    if start_date:
        q = q.filter(Receipt.purchase_date >= start_date)
    if end_date:
        q = q.filter(Receipt.purchase_date <= end_date)
    q = q.group_by(Category.name).order_by(func.sum(LineItem.line_total).desc())

    return [{"category": name, "total": float(total)} for name, total in q.all()]
