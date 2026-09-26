"""Pydantic schemas used at the boundary between components.

Parsed OCR output is validated into `ParsedReceipt` before it's allowed to
touch the database — this is where FR-4 (parsing) and the "reject malformed
data" ingestion requirement are enforced in code, not just documentation.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field, field_validator


class ParsedLineItem(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    quantity: float = Field(default=1.0, gt=0)
    unit_price: float | None = Field(default=None, ge=0)
    line_total: float = Field(ge=0)


class ParsedReceipt(BaseModel):
    merchant_name: str | None = None
    purchase_date: dt.date | None = None
    subtotal: float | None = Field(default=None, ge=0)
    tax: float | None = Field(default=None, ge=0)
    total: float | None = Field(default=None, ge=0)
    line_items: list[ParsedLineItem] = Field(default_factory=list)
    raw_ocr_text: str | None = None

    @field_validator("total")
    @classmethod
    def total_is_plausible(cls, v: float | None, info) -> float | None:
        """Reject obviously-wrong totals (e.g. OCR misread $12.99 as $1299).

        This is a cheap sanity check, not a full reconciliation — real
        subtotal+tax==total checking happens in the ingestion service, where
        a mismatch is logged (FR-14) rather than silently dropped.
        """
        if v is not None and v > 100_000:
            raise ValueError("total exceeds plausible receipt amount")
        return v
