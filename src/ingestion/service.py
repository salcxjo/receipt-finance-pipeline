"""Ingestion service: turns a ParsedReceipt into persisted DB rows.

Responsibilities kept explicit and testable:
- resolve-or-create the merchant
- write the receipt + line items in one transaction (atomic — no partial
  receipts on failure)
- log every attempt, success or failure, with a reason (FR-14)
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from db.models import LineItem, Merchant, Receipt
from src.common.schemas import ParsedReceipt

logger = logging.getLogger("ingestion")


class IngestionError(Exception):
    """Raised when a parsed receipt fails validation/consistency checks."""


def _get_or_create_merchant(session: Session, name: str | None) -> Merchant | None:
    if not name:
        return None
    merchant = session.query(Merchant).filter_by(name=name).one_or_none()
    if merchant is None:
        merchant = Merchant(name=name)
        session.add(merchant)
        session.flush()
    return merchant


def ingest_parsed_receipt(
    session: Session, parsed: ParsedReceipt, image_path: str
) -> Receipt:
    """Persist a validated ParsedReceipt. Raises IngestionError on failure.

    Consistency check: if subtotal, tax, and total are all present, they
    should roughly reconcile. A mismatch doesn't block ingestion (OCR is
    noisy) but is logged so it surfaces for review (FR-8).
    """
    if parsed.subtotal is not None and parsed.tax is not None and parsed.total is not None:
        expected = round(parsed.subtotal + parsed.tax, 2)
        if abs(expected - parsed.total) > 0.02:
            logger.warning(
                "receipt total mismatch: subtotal+tax=%.2f but total=%.2f (image=%s)",
                expected,
                parsed.total,
                image_path,
            )

    try:
        merchant = _get_or_create_merchant(session, parsed.merchant_name)

        receipt = Receipt(
            merchant=merchant,
            purchase_date=parsed.purchase_date,
            subtotal=parsed.subtotal,
            tax=parsed.tax,
            total=parsed.total,
            image_path=image_path,
            raw_ocr_text=parsed.raw_ocr_text,
        )
        for item in parsed.line_items:
            receipt.line_items.append(
                LineItem(
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                )
            )

        session.add(receipt)
        session.commit()
        logger.info("ingested receipt id=%s image=%s", receipt.id, image_path)
        return receipt

    except Exception as exc:
        session.rollback()
        logger.error("ingestion failed for image=%s: %s", image_path, exc)
        raise IngestionError(str(exc)) from exc
