"""Customer model definition."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.purchase import Purchase


class Customer(Base):
    """Represents a customer in the billing system."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
