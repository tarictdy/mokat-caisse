from __future__ import annotations

import sys


def ensure_supported_python() -> None:
    """PyQt6 support in production is currently targeted for Python 3.10-3.12."""
    if sys.version_info >= (3, 13):
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise RuntimeError(
            "Version Python non supportée pour ce build PyQt6. "
            f"Version détectée: {version}. Utilisez Python 3.12 (recommandé) ou 3.10/3.11."
        )
