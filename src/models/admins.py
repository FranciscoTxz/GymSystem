from datetime import datetime
from typing import ClassVar
from zoneinfo import ZoneInfo

from mongoengine import (
    BooleanField,
    DateField,
    DateTimeField,
    Document,
    EmailField,
    StringField,
)

from schemas.admin_schema import AdminType


class Admins(Document):
    email = EmailField(primary_key=True, default=None)
    password_hash = StringField(required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    full_name = StringField(required=True)
    birthdate = DateField(default=None)
    phone_number = StringField(default=None)
    type = StringField(default=AdminType.MID)
    last_login = DateTimeField(default=datetime.now(tz=ZoneInfo("America/Mexico_City")))
    enabled = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now(tz=ZoneInfo("America/Mexico_City")))

    meta: ClassVar[dict[str, object]] = {
        "collection": "admins",
        "indexes": ["full_name"],
    }
