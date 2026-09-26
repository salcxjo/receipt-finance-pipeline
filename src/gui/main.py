"""Desktop GUI entrypoint (FR-7, FR-8, FR-10).

The GUI talks to the REST API (not the DB directly) so it exercises the same
contract as any other client and stays swappable/testable independent of the
backend. Business logic (formatting, filtering) lives in src/gui/widgets so
it can be unit tested with pytest-qt without spinning up the whole app.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from src.gui.views.receipt_browser import ReceiptBrowserView
from src.gui.views.spending_summary import SpendingSummaryView


class MainWindow(QMainWindow):
    def __init__(self, api_base_url: str = "http://localhost:8000") -> None:
        super().__init__()
        self.setWindowTitle("Receipt & Finance Pipeline")
        self.resize(1000, 700)

        tabs = QTabWidget()
        tabs.addTab(ReceiptBrowserView(api_base_url), "Receipts")
        tabs.addTab(SpendingSummaryView(api_base_url), "Spending Summary")
        self.setCentralWidget(tabs)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
