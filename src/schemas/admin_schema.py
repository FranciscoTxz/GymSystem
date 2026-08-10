import re
import unicodedata
from datetime import date, datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHONE_RE = re.compile(r"^\d{10,12}$")
PASSWORD_WHITELIST = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])(?!.*[\s~\\])[a-zA-Z\d!@#$%^&*]+$"
)
PASSWORD_REJECT = "Password must contain uppercase letters, lowercase letters, numbers, and special characters !@#$%^&*."


class AdminType(StrEnum):
    MAX = "MAX"
    MID = "MID"
    LOW = "LOW"


class AdminInfo(BaseModel):
    email: EmailStr
    full_name: str
    birthdate: date | None
    phone_number: str | None
    type: AdminType


class AdminInfoFull(AdminInfo):
    password_hash: str
    first_name: str
    last_name: str
    last_login: datetime


class LogInAdmin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)


class SignUpAdmin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    birthdate: date | None
    phone_number: str | None
    type: AdminType = Field(default=AdminType.MID)

    @field_validator("password")
    def password_must_have(cls, v: str):
        if not PASSWORD_WHITELIST.fullmatch(v):
            raise HTTPException(
                status_code=400,
                detail=PASSWORD_REJECT,
            )
        return v

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
        if v and not PHONE_RE.fullmatch(v.strip()):
            raise HTTPException(
                status_code=400,
                detail="Phone number must be 10 to 12 digits",
            )
        return v

    @field_validator("birthdate", mode="before")
    def date_must_be_iso_format(cls, v):
        if v and isinstance(v, str) and not DATE_RE.fullmatch(v):
            raise HTTPException(
                status_code=400, detail="date must be in 'YYYY-MM-DD' ISO format"
            )
        return v

    @field_validator("birthdate")
    def check_age(cls, v: date):
        if not v:
            return v
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


class AdminPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=16)
    new_password: str = Field(..., min_length=8, max_length=16)

    @field_validator("new_password")
    def password_must_have(cls, v: str):
        if not PASSWORD_WHITELIST.fullmatch(v):
            raise HTTPException(
                status_code=400,
                detail=PASSWORD_REJECT,
            )
        return v


class UpdateAdmin(BaseModel):
    phone_number: str | None = None
    type: AdminType | None = None

    @field_validator("phone_number")
    def phone_must_be_polish_format(cls, v: str):
        if v and not PHONE_RE.fullmatch(v.strip()):
            raise HTTPException(
                status_code=400,
                detail="Phone number must be 10 to 12 digits",
            )
        return v

    @field_validator("phone_number", "type", mode="before")
    def at_least_one_field(cls, v, info):
        if info.data == {} and v is None:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided",
            )
        return v
