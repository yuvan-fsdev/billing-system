"""FastAPI application entry point."""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import models  # noqa: F401  # ensure model metadata is imported
from app.api import routes_billing, routes_purchases
from app.api.serializers import serialize_purchase
from app.db.session import Base, engine, get_db
from app.repositories.purchases import PurchaseRepository


app = FastAPI(title="Billing System API")

base_path = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(base_path / "templates"))

app.mount("/static", StaticFiles(directory=str(base_path / "static")), name="static")


@app.on_event("startup")
def on_startup() -> None:
    """Create database tables on application startup."""
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


app.include_router(routes_billing.router)
app.include_router(routes_purchases.router)


@app.get("/", response_class=HTMLResponse)
def page_one(request: Request) -> HTMLResponse:
    """Render the billing form placeholder."""
    return templates.TemplateResponse("page1.html", {"request": request})


@app.get("/invoice/{purchase_id}", response_class=HTMLResponse)
def invoice_page(
    purchase_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Render an invoice page using stored purchase data."""
    repo = PurchaseRepository(db)
    purchase = repo.get_purchase_with_details(purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    summary = serialize_purchase(purchase)
    return templates.TemplateResponse("page2.html", {"request": request, "invoice": summary.model_dump()})
