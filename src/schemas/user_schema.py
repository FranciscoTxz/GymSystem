import re
import unicodedata
from datetime import date, datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHONE_RE = re.compile(r"^\d{10,12}$")


class UserState(StrEnum):
    active = "ACTIVE"
    deactivated = "DEACTIVATED"
    banned = "BANNED"


class UserInfo(BaseModel):
    id: int
    membership: str
    full_name: str
    birthdate: date
    phone_number: str
    photo_url: str | None
    state: UserState


class UserInfoFull(UserInfo):
    first_name: str
    last_name: str
    phone_number: str
    email: EmailStr | None
    emergency_contact: str
    fingerprint_template: bytes | None
    last_visit: datetime
    next_payment: date
    enabled: bool
    created_at: datetime


class CreateUser(BaseModel):
    membership: str = Field(min_length=3, max_length=20)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    birthdate: date
    phone_number: str = Field(..., min_length=11, max_length=13)
    email: EmailStr | None
    emergency_contact: str = Field(min_length=3)
    photo_url: str | None
    fingerprint_template: bytes | None  # TODO: Validate

    @field_validator("first_name", "last_name")
    def name_must_be_alpha(cls, v: str):
        def is_latin(c: str) -> bool:
            try:
                return "LATIN" in unicodedata.name(c)
            except ValueError:
                return False

        if not v or all(c.isspace() or is_latin(c) for c in v):
            return v
        raise HTTPException(
            status_code=400, detail="Name must contain only Latin alphabetic characters"
        )

    @field_validator("phone_number")
    def phone_must_be_polish_format(cls, v: str):
        if not PHONE_RE.fullmatch(v.strip()):
            raise HTTPException(
                status_code=400,
                detail="Phone number must be in the format that begins with '+' followed by 10 to 12 digits",
            )
        return v

    @field_validator("birthdate", mode="before")
    def date_must_be_iso_format(cls, v):
        if isinstance(v, str) and not DATE_RE.fullmatch(v):
            raise HTTPException(
                status_code=400, detail="date must be in 'YYYY-MM-DD' ISO format"
            )
        return v

    @field_validator("birthdate")
    def check_age(cls, v: date):
        today = datetime.now(tz=ZoneInfo("America/Mexico_City")).date()
        month_day_passed = (today.month, today.day) < (v.month, v.day)
        age = today.year - v.year - (1 if month_day_passed else 0)
        if age < 18:
            raise HTTPException(
                status_code=400, detail="User must be at least 18 years old"
            )
        if age > 120:
            raise HTTPException(
                status_code=400,
                detail="User age seems invalid (greater than 120 years)",
            )
        return v


class UpdateUser(BaseModel):
    phone_number: str | None = None
    email: EmailStr | None = None
    emergency_contact: str | None = None
    photo_url: str | None = None

    @field_validator(
        "phone_number", "email", "emergency_contact", "photo_url", mode="after"
    )
    def at_least_one_field(cls, v, info):
        if all(field_value is None for field_value in info.data.values()):
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided",
            )
        return v


class UpdateMembershipUser(BaseModel):
    membership: str = Field(..., min_length=3, max_length=20)
