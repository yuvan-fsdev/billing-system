"""Common schema utilities."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DecimalModel(BaseModel):
    """Base model providing decimal serialization behaviour."""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: lambda v: format(v, "f")},
    )
