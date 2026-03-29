from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.maintenance import MaintenanceAccess, MaintenanceAudit


class MaintenanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_access_by_username(self, username: str) -> MaintenanceAccess | None:
        stmt = select(MaintenanceAccess).where(MaintenanceAccess.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_accesses(self) -> list[MaintenanceAccess]:
        stmt = select(MaintenanceAccess).order_by(MaintenanceAccess.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def add_access(self, access: MaintenanceAccess) -> MaintenanceAccess:
        self.session.add(access)
        self.session.flush()
        return access

    def add_audit(self, audit: MaintenanceAudit) -> MaintenanceAudit:
        self.session.add(audit)
        self.session.flush()
        return audit

    def list_audits(self, limit: int = 200) -> list[MaintenanceAudit]:
        stmt = select(MaintenanceAudit).order_by(MaintenanceAudit.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())
