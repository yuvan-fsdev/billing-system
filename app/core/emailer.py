"""Simple email helper used with FastAPI BackgroundTasks."""

from typing import Any, Dict


def send_invoice_email(purchase_id: int, recipient: str, summary: Dict[str, Any]) -> None:
    """Stub email sender - replace with real integration as needed."""
    print(f"[EMAIL] Sent invoice #{purchase_id} to {recipient}: {summary['net_price']}")
