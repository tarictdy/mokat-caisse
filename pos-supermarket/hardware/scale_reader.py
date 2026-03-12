from __future__ import annotations

from decimal import Decimal


class ScaleReader:
    """Scale reader for weighted products."""

    def read_weight_kg(self) -> Decimal:
        return Decimal("0")
