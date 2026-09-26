"""Spending-by-category summary view (FR-10). Chart rendering TBD — start
with a simple table, add a bar chart (QtCharts) once the data layer is solid.
"""

from __future__ import annotations

import httpx
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from src.gui.views.receipt_browser import format_amount


class SpendingSummaryView(QWidget):
    def __init__(self, api_base_url: str) -> None:
        super().__init__()
        self.api_base_url = api_base_url

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Category", "Total"])

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        try:
            response = httpx.get(f"{self.api_base_url}/receipts/summary/by-category", timeout=5.0)
            response.raise_for_status()
            rows = response.json()
        except httpx.HTTPError:
            rows = []

        self.table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(item["category"]))
            self.table.setItem(row, 1, QTableWidgetItem(format_amount(item["total"])))
