from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.app_config import DB_PATH


class Base(DeclarativeBase):
    pass


engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


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
