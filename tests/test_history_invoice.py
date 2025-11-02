"""Tests for purchase retrieval and history endpoints."""


def test_purchase_summary_and_history(test_client):
    client = test_client
    SessionLocal = client.session_local

    with SessionLocal() as session:
        # Seed required products and denominations
        from decimal import Decimal
        from app.models.product import Product
        from app.models.denomination import DenominationStock

        session.add(
            Product(
                name="History Item",
                product_code="HIST-1",
                available_stocks=3,
                unit_price=Decimal("50.00"),
                tax_percentage=Decimal("5.00"),
            )
        )
        session.add_all(
            [
                DenominationStock(value=100, available_count=2),
                DenominationStock(value=20, available_count=3),
            ]
        )
        session.commit()

    payload = {
        "customer_email": "history@example.com",
        "items": [{"product_code": "HIST-1", "quantity": 2}],
        "denominations": {
            "counts": {"200": 1},
            "paid_amount": "200.00",
        },
    }
    create_resp = client.post("/api/billing/generate", json=payload)
    assert create_resp.status_code == 201
    purchase_id = create_resp.json()["purchase_id"]

    detail_resp = client.get(f"/api/purchases/{purchase_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["purchase_id"] == purchase_id
    assert detail["total_price_without_tax"] == "100.00"
    assert len(detail["lines"]) == 1

    history_resp = client.get("/api/purchases/history", params={"email": "history@example.com"})
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) == 1
    assert history[0]["id"] == purchase_id
