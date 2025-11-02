"""Purchase repository helpers."""

from decimal import Decimal
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.customer import Customer
from app.models.denomination import ChangeBreakdown, PaymentBreakdown
from app.models.purchase import Purchase, PurchaseItem
from app.services.billing import BillComputation


class PurchaseRepository:
    """Repository encapsulating purchase persistence and retrieval."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_purchase(
        self,
        customer: Customer,
        bill: BillComputation,
        paid_amount: Decimal,
        payment_map: Dict[int, int],
        change_map: Dict[int, int],
        change_remainder: int,
    ) -> Purchase:
        """Persist purchase with denormalised items and denomination breakdowns."""
        purchase = Purchase(
            customer_id=customer.id,
            subtotal=bill.subtotal,
            tax_total=bill.tax_total,
            grand_total=bill.net_total,
            rounded_total=bill.rounded_total,
            paid_amount=paid_amount,
        )
        self.session.add(purchase)
        self.session.flush()

        for line in bill.lines:
            item = PurchaseItem(
                purchase_id=purchase.id,
                product_id=line.product_id,
                product_code=line.product_code,
                product_name=line.product_name,
                quantity=line.quantity,
                unit_price=line.unit_price,
                tax_percentage=line.tax_percentage,
                line_subtotal=line.purchase_price,
                line_tax=line.tax_payable_for_item,
                line_total=line.total_price_of_item,
            )
            self.session.add(item)

        payment_breakdown = PaymentBreakdown(
            purchase_id=purchase.id,
            details_json={"denominations": payment_map},
        )
        change_breakdown = ChangeBreakdown(
            purchase_id=purchase.id,
            details_json={
                "denominations": change_map,
                "remainder": change_remainder,
            },
        )
        self.session.add(payment_breakdown)
        self.session.add(change_breakdown)

        return purchase

    def get_purchase_with_details(self, purchase_id: int) -> Purchase | None:
        """Fetch a purchase with related entities eager-loaded."""
        stmt = (
            select(Purchase)
            .where(Purchase.id == purchase_id)
            .options(
                selectinload(Purchase.customer),
                selectinload(Purchase.items).selectinload(PurchaseItem.product),
                selectinload(Purchase.payment_breakdown),
                selectinload(Purchase.change_breakdown),
            )
        )
        return self.session.execute(stmt).scalars().first()

    def list_purchases_for_customer(self, email: str) -> List[Purchase]:
        """Return purchases for a customer ordered by newest first."""
        stmt = (
            select(Purchase)
            .join(Purchase.customer)
            .where(Customer.email == email)
            .options(selectinload(Purchase.customer))
            .order_by(Purchase.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())
