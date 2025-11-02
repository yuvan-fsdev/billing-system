"""Customer repository helpers."""

from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    """Repository for customer lookups and persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_by_email(self, email: str) -> Customer:
        """Fetch existing customer by email or create a new record."""
        customer = (
            self.session.query(Customer)
            .filter(Customer.email == email)
            .first()
        )
        if customer is not None:
            return customer

        customer = Customer(email=email)
        self.session.add(customer)
        self.session.flush()
        return customer
