from src.ml.inference.ocr_parser import parse_receipt_text

SAMPLE_RECEIPT_TEXT = """\
SUPERSTORE #4021
MILK 2% 4L         2 x $5.49
BREAD WHITE             $3.29
BANANAS                 $2.14
SUBTOTAL               $10.92
TAX                      $0.55
TOTAL                   $11.47
"""
def test_price_digits_are_not_mistaken_for_quantity() -> None:
    result = parse_receipt_text("APPLE GALA SLB HRJ 10.00")

    assert result.line_items[0].quantity == 1
    assert result.line_items[0].line_total == 10.0

def test_parses_line_items() -> None:
    result = parse_receipt_text(SAMPLE_RECEIPT_TEXT)

    descriptions = [item.description for item in result.line_items]
    assert "BREAD WHITE" in descriptions
    assert "BANANAS" in descriptions


def test_parses_total_and_tax_not_subtotal() -> None:
    result = parse_receipt_text(SAMPLE_RECEIPT_TEXT)

    assert result.total == 11.47
    assert result.tax == 0.55


def test_quantity_and_unit_price_extracted() -> None:
    result = parse_receipt_text(SAMPLE_RECEIPT_TEXT)

    milk = next(item for item in result.line_items if "MILK" in item.description)
    assert milk.quantity == 2
    assert milk.unit_price == 5.49


def test_empty_text_returns_no_line_items() -> None:
    result = parse_receipt_text("")

    assert result.line_items == []
    assert result.total is None
