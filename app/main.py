"""FastAPI application entry point."""

from fastapi import FastAPI

from app.db.session import Base, engine
from app import models  # noqa: F401  # ensure model metadata is imported


app = FastAPI(title="Billing System API")


@app.on_event("startup")
def on_startup() -> None:
    """Create database tables on application startup."""
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}
