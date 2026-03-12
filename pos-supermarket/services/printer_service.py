from __future__ import annotations

from hardware.cash_drawer import CashDrawer
from hardware.receipt_printer import ReceiptPrinter


class PrinterService:
    def __init__(self) -> None:
        self.printer = ReceiptPrinter()
        self.cash_drawer = CashDrawer()

    def print_and_cut(self, receipt_text: str, open_drawer: bool = False) -> bool:
        if not self.printer.connect_printer():
            return False
        if not self.printer.print_receipt(receipt_text):
            return False
        self.printer.cut_paper()
        if open_drawer:
            self.cash_drawer.open_cash_drawer()
        return True
