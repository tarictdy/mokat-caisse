from __future__ import annotations

from PyQt6.QtWidgets import QPushButton, QWidget


class IconButton(QPushButton):
    """Styled action button with an optional short text prefix."""

    _VARIANT_NAMES = {
        "primary":   "",
        "secondary": "SecondaryButton",
        "danger":    "DangerButton",
        "success":   "SuccessButton",
    }

    def __init__(
        self,
        text: str,
        icon_text: str = "",
        variant: str = "primary",
        parent: QWidget | None = None,
    ) -> None:
        label = f"{icon_text}  {text}".strip() if icon_text else text
        super().__init__(label, parent)
        self.setMinimumHeight(36)
        obj_name = self._VARIANT_NAMES.get(variant, "")
        if obj_name:
            self.setObjectName(obj_name)
