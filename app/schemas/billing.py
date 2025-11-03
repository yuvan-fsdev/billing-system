"""Billing request and response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from pydantic import BaseModel, EmailStr, Field, condecimal, conint, field_validator

from app.schemas.common import DecimalModel


class LineItemIn(BaseModel):
    """Request payload for a single line item."""

    product_code: str = Field(..., min_length=1)
    quantity: conint(strict=True, ge=1)


class DenominationIn(BaseModel):
    """Denomination details submitted with the bill."""

    counts: Dict[int, int] = Field(default_factory=dict)
    paid_amount: condecimal(max_digits=14, decimal_places=2)

    @field_validator("counts", mode="before")
    @classmethod
    def convert_keys(cls, value: Dict[int | str, int] | None) -> Dict[int, int]:
        if value is None:
            return {}
        converted: Dict[int, int] = {}
        for key, count in value.items():
            converted[int(key)] = int(count)
        return converted

    @field_validator("counts")
    @classmethod
    def validate_counts(cls, value: Dict[int, int]) -> Dict[int, int]:
        for denom, count in value.items():
            if denom <= 0 or count < 0:
                raise ValueError("Denominations must be positive with non-negative counts")
        return value


class BillCreateIn(BaseModel):
    """Complete bill creation request."""

    customer_email: EmailStr
    items: List[LineItemIn]
    denominations: DenominationIn


class PurchaseLineOut(DecimalModel):
    """Response representation of a purchase line item."""

    product_id: int
    product_code: str
    product_name: str
    unit_price: Decimal
    quantity: int
    tax_percentage: Decimal
    purchase_price: Decimal
    tax_payable_for_item: Decimal
    total_price_of_item: Decimal


class PurchaseSummaryOut(DecimalModel):
    """Full invoice summary."""

    purchase_id: int
    customer_email: EmailStr
    created_at: datetime
    lines: List[PurchaseLineOut]
    total_price_without_tax: Decimal
    total_tax_payable: Decimal
    net_price: Decimal
    rounded_down_net_price: int
    paid_amount: Decimal
    balance_payable_to_customer: Decimal
    balance_denomination: Dict[int, int]
    payment_denomination: Dict[int, int]
    change_remainder: int = 0


class PurchaseListItemOut(DecimalModel):
    """Summary of purchases for history listing."""

    id: int
    created_at: datetime
    grand_total: Decimal
