"""Denomination and payment breakdown models."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.purchase import Purchase


class DenominationStock(Base):
    """Tracks available denomination counts within the store."""

    __tablename__ = "denomination_stocks"
    __table_args__ = (
        UniqueConstraint("value", name="uq_denomination_value"),
        Index("ix_denomination_value_desc", desc("value")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[int] = mapped_column(nullable=False)
    available_count: Mapped[int] = mapped_column(nullable=False, default=0)


class PaymentBreakdown(Base):
    """Stores the denominations received from the customer."""

    __tablename__ = "payment_breakdowns"
    __table_args__ = (
        UniqueConstraint("purchase_id", name="uq_payment_breakdown_purchase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    details_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="payment_breakdown")


class ChangeBreakdown(Base):
    """Stores the denominations returned to the customer as change."""

    __tablename__ = "change_breakdowns"
    __table_args__ = (
        UniqueConstraint("purchase_id", name="uq_change_breakdown_purchase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    details_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="change_breakdown")
