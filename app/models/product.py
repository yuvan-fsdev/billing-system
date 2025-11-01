"""Product model definitions."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.purchase import PurchaseItem


class Product(Base):
    """Represents a product that can be sold."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    available_stocks: Mapped[int] = mapped_column(default=0, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    purchase_items: Mapped[list["PurchaseItem"]] = relationship(
        "PurchaseItem",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
