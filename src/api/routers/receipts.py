"""Receipt endpoints: phone upload, list, get, and category spending summary
(FR-1, FR-2, FR-10, FR-11)."""

import io
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from PIL import Image
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models import Category, LineItem, Receipt
from src.api.deps import get_db, require_api_key
from src.common.config import settings
from src.ingestion.service import IngestionError, ingest_parsed_receipt
from src.ml.inference.ocr_parser import parse_receipt_text, run_ocr

router = APIRouter()

_ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}


@router.post("/upload", status_code=201, dependencies=[Depends(require_api_key)])
def upload_receipt(file: UploadFile, db: Session = Depends(get_db)) -> dict:
    """Accept a receipt photo from the phone, OCR + parse it, and store it.

    A plain `def` (not `async def`) on purpose: OCR is blocking and CPU-bound,
    so FastAPI runs this in its threadpool instead of stalling the event loop.
    v1 does everything synchronously; a job queue is the upgrade path if OCR
    gets slow (see ADR 0004).
    """
    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"File larger than {settings.max_upload_mb} MB")

    # Don't trust the client's filename or Content-Type: decode the bytes.
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
            fmt = img.format
    except Exception as exc:
        raise HTTPException(status_code=422, detail="File is not a readable image") from exc
    ext = _ALLOWED_FORMATS.get(fmt or "")
    if ext is None:
        raise HTTPException(status_code=415, detail=f"Unsupported image format: {fmt}")

    dest_dir = Path(settings.receipt_image_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uuid.uuid4()}.{ext}"  # server-generated name, never the client's
    dest.write_bytes(data)

    parsed = parse_receipt_text(run_ocr(dest))
    try:
        receipt = ingest_parsed_receipt(db, parsed, str(dest))
    except IngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"id": str(receipt.id), "line_items": len(parsed.line_items), "total": parsed.total}


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
