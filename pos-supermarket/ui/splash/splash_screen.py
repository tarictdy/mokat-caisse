from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QLabel, QVBoxLayout, QWidget


class SplashScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(720, 420)

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 36)

        bg = QLabel()
        bg.setPixmap(QPixmap())
        bg.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f172a, stop:1 #1d4ed8);"
            "border-radius:18px;"
        )

        overlay = QVBoxLayout(bg)
        overlay.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Bienvenue sur MOKAT MARKET POS")
        title.setStyleSheet("color:white;font-size:30px;font-weight:700;background:transparent;")
        subtitle = QLabel("Interface de caisse moderne, rapide et fiable")
        subtitle.setStyleSheet("color:#dbeafe;font-size:16px;background:transparent;")
        powered = QLabel("POWERED BY SOCAFTDYINDUSTRUAP")
        powered.setStyleSheet("color:#93c5fd;font-size:12px;font-weight:600;background:transparent;")

        overlay.addStretch()
        overlay.addWidget(title)
        overlay.addWidget(subtitle)
        overlay.addStretch()
        overlay.addWidget(powered, alignment=Qt.AlignmentFlag.AlignRight)

        root.addWidget(bg)

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        self.anim = QPropertyAnimation(effect, b"opacity", self)
        self.anim.setDuration(1400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def start(self) -> None:
        self.anim.start()
