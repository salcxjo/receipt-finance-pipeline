"""Receipt OCR + layout parsing.

Two stages, kept separate on purpose so each is independently testable:
  1. `run_ocr` — image -> raw text (thin wrapper around Tesseract; the only
     part of this file that isn't hand-written logic).
  2. `parse_receipt_text` — raw text -> ParsedReceipt. This is the hand-coded
     part: a line-by-line heuristic/regex parser for v1, with a documented
     seam to swap in a trained sequence-labeling model later (see SRS §8).
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

from src.common.schemas import ParsedLineItem, ParsedReceipt

_LINE_ITEM_RE = re.compile(
    r"^(?P<description>.+?)\s+(?:(?P<qty>\d+)\s*[xX@]\s*)?\$?(?P<price>\d+\.\d{2})$"
)
_TOTAL_RE = re.compile(r"(?i)\btotal\b.*?\$?(\d+\.\d{2})")
_TAX_RE = re.compile(r"(?i)\btax\b.*?\$?(\d+\.\d{2})")


def run_ocr(image_path: Path) -> str:
    """Run Tesseract OCR on a receipt image and return raw text.

    Kept as a one-line wrapper so it can be swapped for PaddleOCR/cloud OCR
    (see SRS open question) without touching `parse_receipt_text`.
    """
    import pytesseract

    with Image.open(image_path) as img:
        return pytesseract.image_to_string(img)


def parse_receipt_text(raw_text: str) -> ParsedReceipt:
    """Parse raw OCR text into structured receipt data.

    v1 heuristic parser: scans line by line for a "description ... $price"
    pattern to find line items, and separately looks for total/tax lines.
    This is intentionally simple and will misparse messy receipts — that's
    expected; FR-8/FR-9 capture user corrections as future training data for
    a proper trained parser.
    """
    line_items: list[ParsedLineItem] = []
    total: float | None = None
    tax: float | None = None

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if (m := _TOTAL_RE.search(line)) and "subtotal" not in line.lower():
            total = float(m.group(1))
            continue
        if m := _TAX_RE.search(line):
            tax = float(m.group(1))
            continue
        if m := _LINE_ITEM_RE.match(line):
            price = float(m.group("price"))
            qty = float(m.group("qty")) if m.group("qty") else 1.0
            line_items.append(
                ParsedLineItem(
                    description=m.group("description").strip(),
                    quantity=qty,
                    unit_price=price,
                    line_total=round(price*qty,2)
                )
            )

    return ParsedReceipt(
        total=total,
        tax=tax,
        line_items=line_items,
        raw_ocr_text=raw_text,
    )
