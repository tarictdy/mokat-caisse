from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class SplashScreen(QWidget):
    BRANDING_CANDIDATES = ("splash_branding.png", "splash_branding.jpg", "splash_branding.jpeg")

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(720, 400)
        self.setObjectName("LoginRoot")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Main card ──────────────────────────────────────
        card = QFrame()
        card.setObjectName("SplashBg")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(52, 48, 52, 40)
        card_layout.setSpacing(0)

        # Brand row
        brand_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet("color: #2563EB; font-size: 14px; background: transparent;")
        brand_lbl = QLabel("MOKAT MARKET")
        brand_lbl.setStyleSheet(
            "color: #FFFFFF; font-size: 18px; font-weight: 800;"
            "letter-spacing: 3px; background: transparent; margin-left: 8px;"
        )
        brand_row.addWidget(dot)
        brand_row.addWidget(brand_lbl)
        brand_row.addStretch()

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #1E293B; margin: 28px 0 32px 0;")

        # Main title
        title = QLabel("Bienvenue sur\nMOKAT MARKET POS")
        title.setStyleSheet(
            "color: #FFFFFF; font-size: 32px; font-weight: 700;"
            "line-height: 1.3; background: transparent; letter-spacing: -0.5px;"
        )

        # Subtitle
        subtitle = QLabel("Interface de caisse moderne, rapide et fiable")
        subtitle.setStyleSheet(
            "color: #94A3B8; font-size: 15px; background: transparent; margin-top: 10px;"
        )

        # Loading dots
        loading = QLabel("Chargement . . .")
        loading.setStyleSheet(
            "color: #475569; font-size: 12px; background: transparent; margin-top: 32px;"
        )

        # Footer
        powered = QLabel("POWERED BY SOCAFTDYINDUSTRUAP")
        powered.setStyleSheet(
            "color: #1E40AF; font-size: 10px; font-weight: 700;"
            "letter-spacing: 1.5px; background: transparent;"
        )

        branding = QLabel()
        branding.setAlignment(Qt.AlignmentFlag.AlignCenter)
        branding.setStyleSheet("background: transparent;")
        branding.setVisible(False)

        branding_pixmap = self._load_branding_pixmap()
        if branding_pixmap is not None:
            branding.setPixmap(
                branding_pixmap.scaled(
                    560,
                    170,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            branding.setVisible(True)

        card_layout.addLayout(brand_row)
        card_layout.addWidget(div)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(branding)
        card_layout.addWidget(loading)
        card_layout.addStretch()
        card_layout.addWidget(powered, alignment=Qt.AlignmentFlag.AlignRight)

        root.addWidget(card)

        # ── Fade-in animation ──────────────────────────────
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        self.anim = QPropertyAnimation(effect, b"opacity", self)
        self.anim.setDuration(1200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def start(self) -> None:
        self.anim.start()

    def _load_branding_pixmap(self) -> QPixmap | None:
        project_root = Path(__file__).resolve().parents[3]
        app_root = Path(__file__).resolve().parents[2]
        for root in (project_root, app_root):
            for filename in self.BRANDING_CANDIDATES:
                candidate = root / filename
                if candidate.exists():
                    pixmap = QPixmap(str(candidate))
                    if not pixmap.isNull():
                        return pixmap
        return None
