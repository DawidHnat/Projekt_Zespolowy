import re
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

CATEGORIES_VERSION = "pl-driving-categories-v1"
CATEGORIES = (
    "AM",
    "A1",
    "A2",
    "A",
    "B1",
    "B",
    "B+E",
    "C1",
    "C1+E",
    "C",
    "C+E",
    "D1",
    "D1+E",
    "D",
    "D+E",
    "T",
)
Name = Annotated[str, Field(min_length=1, max_length=100)]
Version = Annotated[int, Field(strict=True, ge=1, le=2147483646)]
DriverSort = Literal["name_asc", "name_desc", "vehicles_asc", "vehicles_desc"]


class DriverSearch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: str = Field(default="", max_length=200)
    active: bool | None = Field(default=None, strict=True)
    assigned: bool | None = Field(default=None, strict=True)
    category: str | None = None
    vehicle_id: UUID | None = None
    sort: DriverSort = "name_asc"
    page: int = Field(default=1, strict=True, ge=1)
    page_size: int = Field(default=25, strict=True, ge=1, le=100)


class DriverFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    first_name: Name
    last_name: Name
    identifier: Name
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=254)
    active: bool = Field(default=True, strict=True)
    categories: list[str] = Field(default_factory=list, max_length=len(CATEGORIES))

    @field_validator("first_name", "last_name", "identifier", "phone", mode="before")
    @classmethod
    def plain_text(cls, value, info):
        if value is None:
            return value
        if not isinstance(value, str) or any(
            ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value
        ):
            raise ValueError("Invalid plain text")
        value = value.strip()
        if info.field_name == "phone":
            if not value:
                return None
            if (
                not re.fullmatch(r"[+0-9(). \-]+", value)
                or not 7 <= sum(c.isdigit() for c in value) <= 20
            ):
                raise ValueError("Invalid phone")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def empty_email(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("categories")
    @classmethod
    def known_categories(cls, value):
        if len(value) != len(set(value)) or any(item not in CATEGORIES for item in value):
            raise ValueError("Unknown or repeated category")
        return [item for item in CATEGORIES if item in value]


class DriverPatch(DriverFields):
    version: Version
    first_name: Name | None = None
    last_name: Name | None = None
    identifier: Name | None = None
    active: bool | None = Field(default=None, strict=True)
    categories: list[str] | None = Field(default=None, max_length=len(CATEGORIES))

    @model_validator(mode="after")
    def changes(self):
        if not self.model_fields_set - {"version"}:
            raise ValueError("No changes")
        for field in ("first_name", "last_name", "identifier", "active", "categories"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError("Cannot clear required field")
        return self

    @field_validator("categories")
    @classmethod
    def known_categories(cls, value):
        return None if value is None else super().known_categories(value)


class AssignmentBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Version
    vehicle_id: UUID


class CloseAssignmentBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Version
