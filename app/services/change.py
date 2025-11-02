"""Change computation and denomination helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.denomination import DenominationStock


def normalize_denomination_map(raw_counts: Dict[int | str, int | str]) -> Dict[int, int]:
    """Normalize denomination counts ensuring non-negative integers."""
    cleaned: Dict[int, int] = {}
    for raw_key, raw_value in raw_counts.items():
        try:
            key = int(raw_key)
            value = int(raw_value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Denomination counts must be integer values",
            ) from None

        if key <= 0 or value < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Denominations must be positive and counts non-negative",
            )
        if value == 0:
            continue
        cleaned[key] = value
    return cleaned


def compute_change_with_stock(
    db: Session,
    change_due: int,
) -> Tuple[Dict[int, int], int]:
    """Compute change using available denomination stock (greedy)."""
    if change_due <= 0:
        return {}, change_due

    result: Dict[int, int] = {}
    remaining = change_due

    denomination_rows = db.execute(
        select(DenominationStock).order_by(DenominationStock.value.desc())
    ).scalars()

    for denom in denomination_rows:
        if remaining <= 0:
            break

        take = min(denom.available_count, remaining // denom.value)
        if take > 0:
            result[denom.value] = take
            remaining -= denom.value * take

    return result, remaining


def mutate_denomination_stocks(
    db: Session,
    received_map: Dict[int, int],
    given_map: Dict[int, int],
) -> None:
    """Mutate denomination stocks based on received and returned change."""
    net_changes = defaultdict(int)

    for value, count in received_map.items():
        net_changes[int(value)] += int(count)

    for value, count in given_map.items():
        net_changes[int(value)] -= int(count)

    for value, delta in net_changes.items():
        denom = (
            db.execute(
                select(DenominationStock).where(DenominationStock.value == value)
            )
            .scalars()
            .first()
        )
        if denom is None:
            denom = DenominationStock(value=value, available_count=0)
            db.add(denom)

        denom.available_count += delta
        if denom.available_count < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient denomination stock for value {value}",
            )
