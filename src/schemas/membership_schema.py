from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator


class Membership(BaseModel):
    id: str = Field(min_length=3, max_length=40)
    days: int = Field(ge=1)
    price: float = Field(ge=1)
    description: str = Field(default="None")


class UpdateMembership(BaseModel):
    days: int | None = None
    price: float | None = None
    description: str | None = None

    @field_validator("days")
    def days_format(cls, v: int):
        if v and v <= 0:
            raise HTTPException(
                status_code=400,
                detail="Days must be greater than 0",
            )
        return v

    @field_validator("price")
    def price_format(cls, v: float):
        if v and v <= 0:
            raise HTTPException(
                status_code=400,
                detail="Price must be greater than 0",
            )
        return v

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field(cls, values):
        if not isinstance(values, dict) or not any(
            values.get(field) is not None for field in ("days", "price", "description")
        ):
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided",
            )
        return values
