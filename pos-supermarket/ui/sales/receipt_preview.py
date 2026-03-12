from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class ReceiptPreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Aperçu reçu")
        self.title = QLabel("Reçu de caisse")
        self.text = QTextEdit()
        self.text.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.text)

    def set_receipt(self, receipt_text: str) -> None:
        self.text.setPlainText(receipt_text)
