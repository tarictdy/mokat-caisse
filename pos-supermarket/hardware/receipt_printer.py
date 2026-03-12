from __future__ import annotations


class ReceiptPrinter:
    """Thermal ticket printer adapter (ESC/POS hook)."""

    def connect_printer(self) -> bool:
        # TODO: integrate python-escpos / OS printer settings
        return True

    def print_receipt(self, receipt_text: str) -> bool:
        _ = receipt_text
        return True

    def cut_paper(self) -> bool:
        return True

    def test_print(self) -> bool:
        return self.print_receipt("*** TEST IMPRESSION MOKATSHOP ***")
