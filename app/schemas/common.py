"""Common schema utilities."""

from decimal import Decimal

from pydantic import BaseModel


class DecimalModel(BaseModel):
    """Base model providing decimal serialization behaviour."""

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: format(v, "f"),
        }
