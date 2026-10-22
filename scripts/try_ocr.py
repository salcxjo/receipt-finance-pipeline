from pathlib import Path
from src.ml.inference.ocr_parser import parse_receipt_text, run_ocr

# 1. Automatically locate your project root (one folder up from 'scripts')
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# 2. Build the correct path using forward slashes (Path handles Windows conversion automatically)
image_path = PROJECT_ROOT / "data" / "raw" / "sample1.jpg"

# 3. Process the file
text = run_ocr(image_path)
print("---- RAW OCR TEXT ----")
print(text)

parsed = parse_receipt_text(text)
print("---- PARSED ----")
print("total:", parsed.total, "| tax:", parsed.tax)
for item in parsed.line_items:
    print(item.description, item.quantity, item.line_total)
