from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models.charge import Charge, ChargeCategory, ChargeType
from models.product import Product
from models.sale import Sale
from models.sale_item import SaleItem


@dataclass
class FinanceSummary:
    revenue: Decimal
    sales_count: int
    average_ticket: Decimal
    cogs: Decimal
    gross_profit: Decimal
    total_charges: Decimal
    net_profit: Decimal
    salary_charges: Decimal
    fixed_charges: Decimal
    variable_charges: Decimal


class FinanceReportService:
    def fetch_sales(self, session: Session, start_dt: datetime, end_dt: datetime) -> list[Sale]:
        return list(
            session.query(Sale)
            .filter(Sale.created_at >= start_dt, Sale.created_at < end_dt)
            .order_by(Sale.created_at.desc())
            .limit(300)
            .all()
        )

    def fetch_charges(self, session: Session, start_date, end_date) -> list[Charge]:
        return list(
            session.query(Charge)
            .filter(
                Charge.is_deleted.is_(False),
                Charge.charge_date >= start_date,
                Charge.charge_date <= end_date,
            )
            .order_by(Charge.charge_date.desc(), Charge.created_at.desc())
            .all()
        )

    def compute_cogs(self, session: Session, sales: list[Sale]) -> Decimal:
        if not sales:
            return Decimal("0.00")

        sale_ids = [sale.id for sale in sales]
        rows = (
            session.query(SaleItem.quantity, Product.purchase_price)
            .join(Product, Product.id == SaleItem.product_id)
            .filter(SaleItem.sale_id.in_(sale_ids))
            .all()
        )

        total = Decimal("0.00")
        for qty, purchase_price in rows:
            total += Decimal(qty) * Decimal(str(purchase_price or 0))
        return total

    def summarize(self, session: Session, sales: list[Sale], charges: list[Charge]) -> FinanceSummary:
        revenue = sum((Decimal(str(s.total_amount)) for s in sales), Decimal("0.00"))
        sales_count = len(sales)
        average_ticket = (revenue / sales_count) if sales_count else Decimal("0.00")

        cogs = self.compute_cogs(session, sales)
        gross_profit = revenue - cogs

        total_charges = sum((Decimal(str(charge.amount)) for charge in charges), Decimal("0.00"))
        net_profit = gross_profit - total_charges

        salary_charges = sum(
            (Decimal(str(charge.amount)) for charge in charges if charge.category == ChargeCategory.SALAIRE),
            Decimal("0.00"),
        )
        fixed_charges = sum(
            (Decimal(str(charge.amount)) for charge in charges if charge.charge_type == ChargeType.FIXE),
            Decimal("0.00"),
        )
        variable_charges = sum(
            (Decimal(str(charge.amount)) for charge in charges if charge.charge_type == ChargeType.VARIABLE),
            Decimal("0.00"),
        )

        return FinanceSummary(
            revenue=revenue,
            sales_count=sales_count,
            average_ticket=average_ticket,
            cogs=cogs,
            gross_profit=gross_profit,
            total_charges=total_charges,
            net_profit=net_profit,
            salary_charges=salary_charges,
            fixed_charges=fixed_charges,
            variable_charges=variable_charges,
        )
