from __future__ import annotations

from pathlib import Path

APP_NAME = "POS Supermarket"
APP_VERSION = "0.1.0"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "pos_database.db"
BACKUP_PATH = DATA_DIR / "backup.db"
