from src.gui.views.receipt_browser import format_amount


def test_format_amount_none() -> None:
    assert format_amount(None) == "—"


def test_format_amount_typical() -> None:
    assert format_amount(1234.5) == "$1,234.50"


def test_format_amount_zero() -> None:
    assert format_amount(0) == "$0.00"
