from __future__ import annotations

import shutil

from core.app_config import BACKUP_PATH, DB_PATH


def backup_database() -> None:
    shutil.copy2(DB_PATH, BACKUP_PATH)


def restore_database() -> None:
    shutil.copy2(BACKUP_PATH, DB_PATH)
