from __future__ import annotations


def normalize_barcode(raw: str) -> str:
    return "".join(ch for ch in raw.strip() if ch.isdigit())
