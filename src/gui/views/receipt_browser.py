"""Receipt list/detail view. Formatting helpers are free functions so
pytest-qt tests can check them without needing a running QApplication.
"""

from __future__ import annotations

import httpx
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


def format_amount(value: float | None) -> str:
    """Pure formatting logic, unit-testable in isolation from Qt."""
    if value is None:
        return "—"
    return f"${value:,.2f}"


class ReceiptBrowserView(QWidget):
    def __init__(self, api_base_url: str) -> None:
        super().__init__()
        self.api_base_url = api_base_url

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Date", "Merchant", "Total"])

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        try:
            response = httpx.get(f"{self.api_base_url}/receipts/", timeout=5.0)
            response.raise_for_status()
            receipts = response.json()
        except httpx.HTTPError:
            receipts = []

        self.table.setRowCount(len(receipts))
        for row, receipt in enumerate(receipts):
            self.table.setItem(row, 0, QTableWidgetItem(str(receipt.get("purchase_date", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(receipt.get("merchant") or "Unknown"))
            self.table.setItem(row, 2, QTableWidgetItem(format_amount(receipt.get("total"))))
