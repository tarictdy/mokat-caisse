from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ReceiptPreview(QDialog):
    """Dialogue d'apercu du recu de caisse - Design moderne"""
    
    def __init__(self, receipt_text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Recu de caisse")
        self.setMinimumSize(420, 600)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background: #F8FAFC;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 16)

        title = QLabel("Recu de caisse")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        header_layout.addWidget(title)

        subtitle = QLabel("Apercu avant impression")
        subtitle.setStyleSheet("font-size: 13px; color: #64748B;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Receipt card
        content = QWidget()
        content.setStyleSheet("background: #F8FAFC;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)

        receipt_card = QFrame()
        receipt_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        receipt_inner = QVBoxLayout(receipt_card)
        receipt_inner.setContentsMargins(20, 20, 20, 20)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("""
            QTextEdit {
                background: #FFFFFF;
                border: none;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #1F2937;
                line-height: 1.5;
            }
        """)
        if receipt_text:
            self.text.setPlainText(receipt_text)
        receipt_inner.addWidget(self.text)

        content_layout.addWidget(receipt_card)
        layout.addWidget(content, 1)

        # Footer
        footer = QWidget()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 16, 24, 16)
        footer_layout.setSpacing(12)

        print_btn = QPushButton("Imprimer")
        print_btn.setMinimumHeight(48)
        print_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 24px;
            }
            QPushButton:hover {
                background: #E2E8F0;
            }
        """)
        print_btn.clicked.connect(self._print_receipt)

        close_btn = QPushButton("Fermer")
        close_btn.setMinimumHeight(48)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #000000;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 32px;
            }
            QPushButton:hover {
                background: #333333;
            }
        """)
        close_btn.clicked.connect(self.accept)

        footer_layout.addWidget(print_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(close_btn)
        layout.addWidget(footer)

    def set_receipt(self, receipt_text: str) -> None:
        self.text.setPlainText(receipt_text)

    def _print_receipt(self) -> None:
        from services.printer_service import PrinterService
        printer = PrinterService()
        if printer.print_and_cut(self.text.toPlainText(), open_drawer=True):
            self.accept()
