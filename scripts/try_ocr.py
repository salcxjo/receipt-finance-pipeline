from pathlib import Path

from src.ml.inference.ocr_parser import parse_receipt_text, run_ocr

text = run_ocr(Path("data/raw/sample1.jpeg"))
print("---- RAW OCR TEXT ----")
print(text)

parsed = parse_receipt_text(text)
print("---- PARSED ----")
print("total:", parsed.total, "| tax:", parsed.tax)
for item in parsed.line_items:
    print(item.description, item.quantity, item.line_total)