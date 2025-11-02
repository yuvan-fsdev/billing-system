"""Billing API endpoints."""

from decimal import Decimal, ROUND_DOWN
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.serializers import serialize_purchase
from app.core.emailer import send_invoice_email
from app.db.session import get_db
from app.repositories.customers import CustomerRepository
from app.repositories.products import ProductRepository
from app.repositories.purchases import PurchaseRepository
from app.schemas.billing import BillCreateIn, PurchaseSummaryOut
from app.services.billing import LineRequest, compute_bill, load_lines_or_400
from app.services.change import (
    compute_change_with_stock,
    mutate_denomination_stocks,
    normalize_denomination_map,
)
from app.services.money import q

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.post("/generate", response_model=PurchaseSummaryOut, status_code=status.HTTP_201_CREATED)
def generate_bill(
    payload: BillCreateIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PurchaseSummaryOut:
    """Create a bill, persist purchase, and return invoice summary."""

    product_repo = ProductRepository(db)
    customer_repo = CustomerRepository(db)
    purchase_repo = PurchaseRepository(db)

    line_requests: List[LineRequest] = [
        LineRequest(product_code=item.product_code, quantity=item.quantity)
        for item in payload.items
    ]
    loaded_lines = load_lines_or_400(db, line_requests)
    bill = compute_bill(loaded_lines)

    paid_amount = q(payload.denominations.paid_amount)
    if paid_amount < Decimal(bill.rounded_total):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid amount is less than the rounded bill amount.",
        )

    payment_map = normalize_denomination_map(payload.denominations.counts)
    paid_amount_int = int(paid_amount.quantize(Decimal("1"), rounding=ROUND_DOWN))
    change_due = paid_amount_int - bill.rounded_total
    change_map, change_remainder = compute_change_with_stock(db, change_due)

    purchase_id: int | None = None

    try:
        with db.begin():
            customer = customer_repo.get_or_create_by_email(payload.customer_email)

            purchase = purchase_repo.create_purchase(
                customer=customer,
                bill=bill,
                paid_amount=paid_amount,
                payment_map=payment_map,
                change_map=change_map,
                change_remainder=change_remainder,
            )
            purchase_id = purchase.id

            for loaded_line, computed_line in zip(loaded_lines, bill.lines):
                product_repo.decrement_stock(loaded_line.product, computed_line.quantity)

            mutate_denomination_stocks(db, payment_map, change_map)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if purchase_id is None:
        raise HTTPException(status_code=500, detail="Failed to create purchase.")

    purchase = purchase_repo.get_purchase_with_details(purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found after creation.")

    summary = serialize_purchase(purchase)

    background_tasks.add_task(
        send_invoice_email,
        purchase_id=purchase.id,
        recipient=summary.customer_email,
        summary=summary.dict(),
    )

    return summary
