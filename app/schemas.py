"""Pydantic schemas for the upsell API."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, field_validator


class UpsellRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: StrictInt = Field(gt=0)
    tenure_months: StrictInt = Field(ge=0)
    monthly_spend: StrictFloat = Field(ge=0)
    num_support_tickets: StrictInt = Field(ge=0)

    @field_validator("tenure_months", "num_support_tickets")
    @classmethod
    def non_negative_int(cls, value: int) -> int:
        if value < 0:
            msg = "value must be non-negative"
            raise ValueError(msg)
        return value

    @field_validator("monthly_spend")
    @classmethod
    def non_negative_float(cls, value: float) -> float:
        if value < 0:
            msg = "monthly_spend must be non-negative"
            raise ValueError(msg)
        return value

    @field_validator("age")
    @classmethod
    def positive_age(cls, value: int) -> int:
        if value <= 0:
            msg = "age must be greater than zero"
            raise ValueError(msg)
        return value


class UpsellResponse(BaseModel):
    upsell_probability: float
    upsell_label: bool
    request_id: str
