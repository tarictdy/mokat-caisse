from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.app_config import BACKUP_PATH, BASE_DIR
from core.backup import backup_database


@dataclass
class FirebaseBackupResult:
    success: bool
    message: str
    bucket: str | None = None
    object_path: str | None = None
    file_size: int | None = None
    sent_at: datetime | None = None


class FirebaseBackupService:
    def __init__(self) -> None:
        self._app = None

    def config_status(self) -> dict[str, str]:
        sdk_ok = "oui" if self._is_sdk_available() else "non"
        cred_path = self._credentials_path()
        bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "")
        return {
            "sdk_available": sdk_ok,
            "credentials_path": str(cred_path) if cred_path else "non configure",
            "bucket": bucket or "non configure",
        }

    def upload_backup(self) -> FirebaseBackupResult:
        if not self._is_sdk_available():
            return FirebaseBackupResult(False, "Firebase Admin SDK non installe (pip install firebase-admin).")

        cred_path = self._credentials_path()
        if not cred_path or not cred_path.exists():
            return FirebaseBackupResult(False, "Fichier credentials Firebase introuvable.")

        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "").strip()
        if not bucket_name:
            return FirebaseBackupResult(False, "Variable FIREBASE_STORAGE_BUCKET non configuree.")

        app, storage = self._ensure_app(cred_path, bucket_name)
        if app is None:
            return FirebaseBackupResult(False, "Impossible d'initialiser Firebase Admin.")

        backup_database()
        if not BACKUP_PATH.exists():
            return FirebaseBackupResult(False, "Backup local indisponible.")

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_path = f"mokat_backups/{timestamp}_pos_backup.db"
        bucket = storage.bucket(app=app)
        blob = bucket.blob(object_path)
        blob.upload_from_filename(str(BACKUP_PATH))
        file_size = BACKUP_PATH.stat().st_size
        return FirebaseBackupResult(
            success=True,
            message="Backup envoye vers Firebase Storage.",
            bucket=bucket_name,
            object_path=object_path,
            file_size=file_size,
            sent_at=datetime.utcnow(),
        )

    def _is_sdk_available(self) -> bool:
        try:
            import firebase_admin  # noqa: F401
            return True
        except Exception:
            return False

    def _credentials_path(self) -> Path | None:
        env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if env_path:
            return Path(env_path)
        default_candidates = [
            BASE_DIR.parent / "ts" / "firebase-service-account.json",
            BASE_DIR.parent / "firebase-service-account.json",
            BASE_DIR / "data" / "firebase-service-account.json",
        ]
        for candidate in default_candidates:
            if candidate.exists():
                return candidate
        return default_candidates[0]

    def _ensure_app(self, cred_path: Path, bucket_name: str):
        try:
            import firebase_admin
            from firebase_admin import credentials, storage

            if firebase_admin._apps:  # type: ignore[attr-defined]
                return firebase_admin.get_app(), storage

            cred = credentials.Certificate(str(cred_path))
            app = firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
            return app, storage
        except Exception:
            return None, None
