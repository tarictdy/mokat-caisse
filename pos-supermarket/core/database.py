from __future__ import annotations

import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.app_config import (
    DB_PATH,
    DEFAULT_ADMIN_EMPLOYEE_CODE,
    DEFAULT_ADMIN_NOM,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_PRENOM,
    DEFAULT_ADMIN_USERNAME,
)


class Base(DeclarativeBase):
    pass


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _ensure_product_columns() -> None:
    """Lightweight SQLite migration for existing local DB files."""
    expected_columns = {
        "internal_reference": "TEXT",
        "brand": "TEXT",
        "stock_max": "INTEGER DEFAULT 0",
        "image_path": "TEXT",
        "promotion_eligible": "BOOLEAN DEFAULT 1",
    }

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        existing_tables = {row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "products" not in existing_tables:
            return

        existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(products)")}
        for col_name, col_type in expected_columns.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")

        conn.commit()


def _ensure_sales_columns() -> None:
    """Lightweight SQLite migration for payment tracking fields."""
    expected_columns = {
        "payment_channel": "TEXT DEFAULT 'cash'",
        "transaction_reference": "TEXT",
    }

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        existing_tables = {row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "sales" not in existing_tables:
            return

        existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(sales)")}
        for col_name, col_type in expected_columns.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE sales ADD COLUMN {col_name} {col_type}")

        conn.commit()


def _ensure_default_admin() -> None:
    from core.security import hash_password
    from models.user import User, UserRole

    with SessionLocal() as session:
        existing_admin = session.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if existing_admin:
            return

        admin_user = User(
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            nom=DEFAULT_ADMIN_NOM,
            prenom=DEFAULT_ADMIN_PRENOM,
            employee_code=DEFAULT_ADMIN_EMPLOYEE_CODE,
            telephone=None,
        )
        session.add(admin_user)
        session.commit()


def init_db() -> None:
    # Late import to ensure all models are registered on metadata.
    from models import (
        category,
        product,
        promotion,
        sale,
        sale_item,
        stock_movement,
        supplier,
        user,
    )

    _ = (category, product, promotion, sale, sale_item, stock_movement, supplier, user)
    Base.metadata.create_all(bind=engine)
    _ensure_product_columns()
    _ensure_sales_columns()
    _ensure_default_admin()
