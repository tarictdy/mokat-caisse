from __future__ import annotations


class BarcodeScanner:
    """USB scanner helper (most scanners behave as keyboard input)."""

    def normalize_code(self, raw_value: str) -> str:
        return raw_value.strip()

    def is_valid_scan(self, barcode: str) -> bool:
        return bool(barcode)
