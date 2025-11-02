"""Tests for billing computations."""

from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.product import Product
from app.services.billing import LineRequest, compute_bill, load_lines_or_400
from app.services.money import q


def test_quantize_rounds_half_up():
    assert q("1.005") == Decimal("1.01")
    assert q("1.004") == Decimal("1.00")


def test_load_lines_and_compute_bill(db_session):
    product = Product(
        name="Test Widget",
        product_code="W123",
        available_stocks=10,
        unit_price=Decimal("199.50"),
        tax_percentage=Decimal("18.0"),
    )
    db_session.add(product)
    db_session.commit()

    line_requests = [LineRequest(product_code="W123", quantity=2)]
    loaded_lines = load_lines_or_400(db_session, line_requests)
    bill = compute_bill(loaded_lines)

    assert bill.subtotal == Decimal("399.00")
    assert bill.tax_total == Decimal("71.82")
    assert bill.net_total == Decimal("470.82")
    assert bill.rounded_total == 470
    assert len(bill.lines) == 1
    computed_line = bill.lines[0]
    assert computed_line.product_code == "W123"
    assert computed_line.purchase_price == Decimal("399.00")
    assert computed_line.tax_payable_for_item == Decimal("71.82")
    assert computed_line.total_price_of_item == Decimal("470.82")


def test_load_lines_validates_stock(db_session):
    product = Product(
        name="Limited Item",
        product_code="LIM-1",
        available_stocks=1,
        unit_price=Decimal("10.00"),
        tax_percentage=Decimal("5.0"),
    )
    db_session.add(product)
    db_session.commit()

    with pytest.raises(HTTPException):
        load_lines_or_400(db_session, [LineRequest(product_code="LIM-1", quantity=2)])
