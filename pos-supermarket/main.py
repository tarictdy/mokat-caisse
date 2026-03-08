from __future__ import annotations

import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from core.app_config import APP_NAME, BASE_DIR
from core.database import init_db
from ui.login.login_window import LoginWindow
from ui.splash.splash_screen import SplashScreen


def main() -> int:
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    qss_path = BASE_DIR / "assets" / "styles" / "app.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    splash = SplashScreen()
    splash.show()
    splash.start()

    window = LoginWindow()

    def show_login() -> None:
        splash.close()
        window.show()

    QTimer.singleShot(1900, show_login)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
