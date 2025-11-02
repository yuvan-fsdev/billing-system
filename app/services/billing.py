"""Billing computation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Iterable, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.money import q


@dataclass(slots=True)
class LineRequest:
    """Incoming line request containing product code and quantity."""

    product_code: str
    quantity: int


@dataclass(slots=True)
class LoadedLine:
    """Hydrated product and quantity data for computation."""

    product: Product
    quantity: int


@dataclass(slots=True)
class ComputedLine:
    """Computed figures for a single line item."""

    product_id: int
    product_code: str
    product_name: str
    unit_price: Decimal
    quantity: int
    tax_percentage: Decimal
    purchase_price: Decimal
    tax_payable_for_item: Decimal
    total_price_of_item: Decimal


@dataclass(slots=True)
class BillComputation:
    """Aggregate computation for a bill."""

    subtotal: Decimal
    tax_total: Decimal
    net_total: Decimal
    rounded_total: int
    lines: List[ComputedLine]


def load_lines_or_400(db: Session, items: Iterable[LineRequest]) -> List[LoadedLine]:
    """Resolve product codes to Product entities and validate stock."""

    lines: List[LoadedLine] = []
    for item in items:
        product: Product | None = (
            db.query(Product)
            .filter(Product.product_code == item.product_code)
            .first()
        )
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with code '{item.product_code}' not found",
            )

        if item.quantity < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quantity for product '{item.product_code}' must be at least 1",
            )

        if item.quantity > product.available_stocks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product '{item.product_code}'",
            )

        lines.append(LoadedLine(product=product, quantity=int(item.quantity)))

    if not lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one line item is required",
        )

    return lines


def compute_bill(lines: Iterable[LoadedLine]) -> BillComputation:
    """Compute per-line and aggregate totals for the bill."""

    subtotal = Decimal("0.00")
    tax_total = Decimal("0.00")
    computed_lines: List[ComputedLine] = []

    for line in lines:
        unit_price = q(line.product.unit_price)
        quantity = int(line.quantity)
        purchase_price = q(unit_price * quantity)
        tax_percentage = q(line.product.tax_percentage)
        line_tax = q(purchase_price * (tax_percentage / Decimal("100")))
        line_total = q(purchase_price + line_tax)

        subtotal = q(subtotal + purchase_price)
        tax_total = q(tax_total + line_tax)

        computed_lines.append(
            ComputedLine(
                product_id=line.product.id,
                product_code=line.product.product_code,
                product_name=line.product.name,
                unit_price=unit_price,
                quantity=quantity,
                tax_percentage=tax_percentage,
                purchase_price=purchase_price,
                tax_payable_for_item=line_tax,
                total_price_of_item=line_total,
            )
        )

    net_total = q(subtotal + tax_total)
    rounded_total = int(net_total.quantize(Decimal("1"), rounding=ROUND_DOWN))

    return BillComputation(
        subtotal=subtotal,
        tax_total=tax_total,
        net_total=net_total,
        rounded_total=rounded_total,
        lines=computed_lines,
    )
