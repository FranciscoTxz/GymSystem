from datetime import datetime
from typing import ClassVar
from zoneinfo import ZoneInfo

from mongoengine import (
    BinaryField,
    BooleanField,
    DateField,
    DateTimeField,
    Document,
    EmailField,
    IntField,
    StringField,
    URLField,
)

from schemas.user_schema import UserState


class Users(Document):
    id = IntField(primary_key=True, required=True)
    membership = StringField(required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    full_name = StringField(required=True)
    birthdate = StringField(required=True)
    phone_number = StringField(required=True)
    email = EmailField(default=None)
    emergency_contact = StringField(required=True)
    photo_url = URLField(default=None)
    state = StringField(default=UserState.active)
    fingerprint_template = BinaryField(default=None)
    last_visit = DateTimeField(default=datetime.now(tz=ZoneInfo("America/Mexico_City")))
    next_payment = DateField(required=True)
    enabled = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now(tz=ZoneInfo("America/Mexico_City")))

    meta: ClassVar[dict[str, object]] = {
        "collection": "users",
        "indexes": ["full_name"],
    }
