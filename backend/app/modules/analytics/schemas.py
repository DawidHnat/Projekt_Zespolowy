from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Threshold = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=1, allow_inf_nan=False)]


class RuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["daily_distance_threshold"] = "daily_distance_threshold"
    threshold_km: Threshold
    vehicle_id: UUID | None = None
    active: bool = Field(default=True, strict=True)

    @field_validator("threshold_km", mode="before")
    @classmethod
    def reject_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("Próg musi być liczbą kilometrów")
        return value


class RuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    threshold_km: Threshold | None = None
    vehicle_id: UUID | None = None
    active: bool | None = Field(default=None, strict=True)

    @field_validator("threshold_km", mode="before")
    @classmethod
    def reject_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("Próg musi być liczbą kilometrów")
        return value

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("Podaj zmieniane pola")
        for field in ("threshold_km", "active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError("Próg i aktywność nie mogą być puste")
        return self


class ReceiptBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    read: bool = Field(strict=True)
