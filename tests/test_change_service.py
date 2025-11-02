"""Tests for change computation and denomination mutations."""

import pytest
from fastapi import HTTPException

from app.models.denomination import DenominationStock
from app.services.change import (
    compute_change_with_stock,
    mutate_denomination_stocks,
    normalize_denomination_map,
)


def test_normalize_denomination_map():
    raw = {"200": "2", 100: 1}
    cleaned = normalize_denomination_map(raw)
    assert cleaned == {200: 2, 100: 1}


def test_normalize_rejects_invalid_entries():
    with pytest.raises(HTTPException):
        normalize_denomination_map({0: 1})


def test_compute_change_respects_stock(db_session):
    db_session.add_all(
        [
            DenominationStock(value=100, available_count=1),
            DenominationStock(value=50, available_count=2),
            DenominationStock(value=20, available_count=0),
        ]
    )
    db_session.commit()

    change_map, remainder = compute_change_with_stock(db_session, 180)
    assert change_map == {100: 1, 50: 1}
    assert remainder == 30


def test_mutate_denomination_stocks_updates_totals(db_session):
    stock = DenominationStock(value=50, available_count=5)
    db_session.add(stock)
    db_session.commit()

    mutate_denomination_stocks(db_session, received_map={50: 2}, given_map={50: 1})
    db_session.flush()

    refreshed = db_session.query(DenominationStock).filter_by(value=50).one()
    assert refreshed.available_count == 6
