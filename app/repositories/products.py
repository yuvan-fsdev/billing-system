"""Product repository helpers."""

from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    """Repository providing product lookups and stock mutation."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_code(self, product_code: str) -> Product | None:
        """Return product matching the provided product code."""
        return (
            self.session.query(Product)
            .filter(Product.product_code == product_code)
            .first()
        )

    def decrement_stock(self, product: Product, quantity: int) -> None:
        """Decrease available stock for a product."""
        product.available_stocks -= quantity
        if product.available_stocks < 0:
            raise ValueError("Product stock cannot be negative")
