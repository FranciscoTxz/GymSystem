from datetime import datetime
from typing import ClassVar

from mongoengine import (
    BooleanField,
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
    birthdate = StringField(default=None)
    phone_number = StringField(default=None)
    type = StringField(default=AdminType.MID)
    last_login = DateTimeField(default=datetime.now)
    enabled = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)

    meta: ClassVar[dict[str, object]] = {
        "collection": "admins",
        "indexes": ["full_name"],
    }
