"""Serializers converting ORM models to response schemas."""

from decimal import Decimal
from typing import Dict, List

from app.models.purchase import Purchase, PurchaseItem
from app.schemas.billing import PurchaseLineOut, PurchaseSummaryOut
from app.services.money import q


def _serialize_line(item: PurchaseItem) -> PurchaseLineOut:
    return PurchaseLineOut(
        product_id=item.product_id,
        product_code=item.product_code,
        product_name=item.product_name,
        unit_price=item.unit_price,
        quantity=item.quantity,
        tax_percentage=item.tax_percentage,
        purchase_price=item.line_subtotal,
        tax_payable_for_item=item.line_tax,
        total_price_of_item=item.line_total,
    )


def serialize_purchase(purchase: Purchase) -> PurchaseSummaryOut:
    """Convert a Purchase ORM object into API response schema."""
    lines: List[PurchaseLineOut] = [_serialize_line(item) for item in purchase.items]

    payment_payload: Dict[str, Dict[int, int]] = purchase.payment_breakdown.details_json if purchase.payment_breakdown else {}
    change_payload: Dict[str, Dict[int, int] | int] = purchase.change_breakdown.details_json if purchase.change_breakdown else {}

    payment_map = payment_payload.get("denominations", {})
    change_map = change_payload.get("denominations", {})
    change_remainder = change_payload.get("remainder", 0)

    balance = q(purchase.paid_amount - Decimal(purchase.rounded_total))

    return PurchaseSummaryOut(
        purchase_id=purchase.id,
        customer_email=purchase.customer.email,
        created_at=purchase.created_at,
        lines=lines,
        total_price_without_tax=purchase.subtotal,
        total_tax_payable=purchase.tax_total,
        net_price=purchase.grand_total,
        rounded_down_net_price=purchase.rounded_total,
        paid_amount=purchase.paid_amount,
        balance_payable_to_customer=balance,
        balance_denomination=change_map,
        payment_denomination=payment_map,
        change_remainder=change_remainder,
    )
