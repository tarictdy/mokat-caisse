from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from core.app_config import APP_NAME
from core.database import init_db
from ui.login.login_window import LoginWindow


def main() -> int:
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = LoginWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
