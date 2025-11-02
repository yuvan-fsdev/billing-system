"""Integration tests for bill generation endpoint."""

from decimal import Decimal

from app.models.denomination import DenominationStock
from app.models.product import Product


def test_generate_bill_flow(test_client):
    client = test_client
    SessionLocal = client.session_local

    with SessionLocal() as session:
        session.add(
            Product(
                name="Sample Item",
                product_code="SKU-1",
                available_stocks=5,
                unit_price=Decimal("100.00"),
                tax_percentage=Decimal("10.00"),
            )
        )
        session.add_all(
            [
                DenominationStock(value=100, available_count=1),
                DenominationStock(value=50, available_count=2),
                DenominationStock(value=20, available_count=2),
                DenominationStock(value=10, available_count=5),
            ]
        )
        session.commit()

    payload = {
        "customer_email": "customer@example.com",
        "items": [{"product_code": "SKU-1", "quantity": 1}],
        "denominations": {
            "counts": {"200": 1},
            "paid_amount": "200.00",
        },
    }

    response = client.post("/api/billing/generate", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()

    assert data["customer_email"] == "customer@example.com"
    assert data["net_price"] == "110.00"
    assert data["rounded_down_net_price"] == 110
    assert data["balance_payable_to_customer"] == "90.00"
    assert data["change_remainder"] == 0
    assert data["payment_denomination"] == {"200": 1}
    assert data["balance_denomination"] == {"50": 1, "20": 2}

    with SessionLocal() as session:
        product = session.query(Product).filter_by(product_code="SKU-1").one()
        assert product.available_stocks == 4
        denom_200 = session.query(DenominationStock).filter_by(value=200).one()
        assert denom_200.available_count == 1
