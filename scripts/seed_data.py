"""Seed database with sample products and denomination stock."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.session import Base, SessionLocal, engine
from app.models.denomination import DenominationStock
from app.models.product import Product


PRODUCT_FIXTURES = [
    {
        "name": "Notebook 200 pages",
        "product_code": "NB200",
        "available_stocks": 100,
        "unit_price": Decimal("45.50"),
        "tax_percentage": Decimal("12.0"),
    },
    {
        "name": "Gel Pen Pack",
        "product_code": "PEN-GEL",
        "available_stocks": 200,
        "unit_price": Decimal("60.00"),
        "tax_percentage": Decimal("18.0"),
    },
    {
        "name": "Desk Organizer",
        "product_code": "DESK-ORG",
        "available_stocks": 40,
        "unit_price": Decimal("349.00"),
        "tax_percentage": Decimal("18.0"),
    },
    {
        "name": "USB-C Cable 1m",
        "product_code": "USBC-1M",
        "available_stocks": 150,
        "unit_price": Decimal("199.00"),
        "tax_percentage": Decimal("18.0"),
    },
    {
        "name": "Wireless Mouse",
        "product_code": "MOUSE-WL",
        "available_stocks": 80,
        "unit_price": Decimal("599.00"),
        "tax_percentage": Decimal("18.0"),
    },
]

DEFAULT_DENOMINATIONS = [2000, 500, 200, 100, 50, 20, 10, 5, 2, 1]


def seed_products(session: Session) -> None:
    """Insert or update product fixtures."""
    for data in PRODUCT_FIXTURES:
        product = (
            session.query(Product)
            .filter(Product.product_code == data["product_code"])
            .first()
        )
        if product:
            for key, value in data.items():
                setattr(product, key, value)
        else:
            session.add(Product(**data))


def seed_denominations(session: Session) -> None:
    """Ensure default denomination rows exist."""
    for value in DEFAULT_DENOMINATIONS:
        denom = (
            session.query(DenominationStock)
            .filter(DenominationStock.value == value)
            .first()
        )
        if denom is None:
            session.add(DenominationStock(value=value, available_count=0))


def main() -> None:
    """Entry point for the seeding script."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_products(session)
        seed_denominations(session)
        session.commit()
    print("Seed data inserted.")


if __name__ == "__main__":
    main()
