"""Email helper used with FastAPI BackgroundTasks."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any, Dict

from app.core.config import settings


def _build_email_body(purchase_id: int, summary: Dict[str, Any]) -> str:
    lines = [
        f"Invoice #{purchase_id}",
        "",
        f"Total (rounded): ₹{summary.get('rounded_down_net_price')}",
        f"Paid amount: ₹{summary.get('paid_amount')}",
        f"Change due: ₹{summary.get('balance_payable_to_customer')} (remainder: ₹{summary.get('change_remainder')})",
        "",
        "Line items:",
    ]
    for item in summary.get("lines", []):
        lines.append(
            f"- {item.get('product_name')} (#{item.get('product_code')}) x{item.get('quantity')} → ₹{item.get('total_price_of_item')}"
        )
    lines.extend(
        [
            "",
            "Thank you for shopping with us.",
        ]
    )
    return "\n".join(lines)


def send_invoice_email(purchase_id: int, recipient: str, summary: Dict[str, Any]) -> None:
    """Send invoice details to the customer via SMTP."""
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        print(f"[EMAIL] SMTP not configured; skipping send for invoice #{purchase_id}")
        return

    message = EmailMessage()
    message["Subject"] = f"Your Invoice #{purchase_id}"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient
    message.set_content(_build_email_body(purchase_id, summary))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
            server.send_message(message)
        print(f"[EMAIL] Invoice #{purchase_id} sent to {recipient}")
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[EMAIL] Failed to send invoice #{purchase_id} to {recipient}: {exc}")
