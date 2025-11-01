"""Purchase and purchase item models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.denomination import ChangeBreakdown, PaymentBreakdown
    from app.models.product import Product


class Purchase(Base):
    """Represents a purchase transaction."""

    __tablename__ = "purchases"
    __table_args__ = (
        Index("ix_purchases_customer_created", "customer_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    rounded_total: Mapped[int] = mapped_column(nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="purchases")
    items: Mapped[list["PurchaseItem"]] = relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    payment_breakdown: Mapped[Optional["PaymentBreakdown"]] = relationship(
        "PaymentBreakdown",
        back_populates="purchase",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    change_breakdown: Mapped[Optional["ChangeBreakdown"]] = relationship(
        "ChangeBreakdown",
        back_populates="purchase",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )


class PurchaseItem(Base):
    """Denormalized purchase line item."""

    __tablename__ = "purchase_items"
    __table_args__ = (
        Index("ix_purchase_items_purchase_product", "purchase_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    line_subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="purchase_items")
