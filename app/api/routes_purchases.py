"""Purchase retrieval endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.api.serializers import serialize_purchase
from app.db.session import get_db
from app.repositories.purchases import PurchaseRepository
from app.schemas.billing import PurchaseListItemOut, PurchaseSummaryOut


router = APIRouter(prefix="/api/purchases", tags=["purchases"])


@router.get("/history", response_model=List[PurchaseListItemOut])
def list_purchase_history(
    email: EmailStr = Query(..., description="Customer email"),
    db: Session = Depends(get_db),
) -> List[PurchaseListItemOut]:
    """List previous purchases for a customer."""
    repo = PurchaseRepository(db)
    purchases = repo.list_purchases_for_customer(email)
    return [
        PurchaseListItemOut(
            id=purchase.id,
            created_at=purchase.created_at,
            grand_total=purchase.grand_total,
        )
        for purchase in purchases
    ]


@router.get("/{purchase_id}", response_model=PurchaseSummaryOut)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
) -> PurchaseSummaryOut:
    """Fetch a purchase invoice by ID."""
    repo = PurchaseRepository(db)
    purchase = repo.get_purchase_with_details(purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")
    return serialize_purchase(purchase)
