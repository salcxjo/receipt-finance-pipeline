from db.models import Receipt
from src.common.schemas import ParsedLineItem, ParsedReceipt
from src.ingestion.service import ingest_parsed_receipt


def test_ingest_creates_receipt_and_line_items(db_session) -> None:
    parsed = ParsedReceipt(
        merchant_name="Superstore",
        total=11.47,
        subtotal=10.92,
        tax=0.55,
        line_items=[
            ParsedLineItem(description="MILK 2% 4L", quantity=2, unit_price=5.49, line_total=10.98),
        ],
    )

    receipt = ingest_parsed_receipt(db_session, parsed, image_path="data/raw/test.jpg")

    stored = db_session.get(Receipt, receipt.id)
    assert stored is not None
    assert stored.merchant.name == "Superstore"
    assert len(stored.line_items) == 1
    assert stored.line_items[0].description == "MILK 2% 4L"


def test_ingest_reuses_existing_merchant(db_session) -> None:
    parsed_a = ParsedReceipt(merchant_name="Cafe Nero", total=5.0, line_items=[])
    parsed_b = ParsedReceipt(merchant_name="Cafe Nero", total=7.5, line_items=[])

    receipt_a = ingest_parsed_receipt(db_session, parsed_a, image_path="a.jpg")
    receipt_b = ingest_parsed_receipt(db_session, parsed_b, image_path="b.jpg")

    assert receipt_a.merchant_id == receipt_b.merchant_id
