from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "POS Supermarket"
APP_VERSION = "0.1.0"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "pos_database.db"
BACKUP_PATH = DATA_DIR / "backup.db"

# Identifiants admin par défaut (surchargeables via variables d'environnement)
DEFAULT_ADMIN_USERNAME = os.getenv("POS_DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("POS_DEFAULT_ADMIN_PASSWORD", "Admin@12345")
DEFAULT_ADMIN_NOM = os.getenv("POS_DEFAULT_ADMIN_NOM", "Super")
DEFAULT_ADMIN_PRENOM = os.getenv("POS_DEFAULT_ADMIN_PRENOM", "Admin")
DEFAULT_ADMIN_EMPLOYEE_CODE = os.getenv("POS_DEFAULT_ADMIN_EMPLOYEE_CODE", "ADM001")
