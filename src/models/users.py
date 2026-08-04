from datetime import datetime
from typing import ClassVar

from mongoengine import (
    BinaryField,
    BooleanField,
    DateTimeField,
    Document,
    EmailField,
    IntField,
    StringField,
    URLField,
)


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
    state = StringField(default="ACTIVE")
    fingerprint_template = BinaryField(default=None)
    last_visit = DateTimeField(default=datetime.now)
    next_payment = DateTimeField(required=True)
    enabled = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)

    meta: ClassVar[dict[str, object]] = {
        "collection": "users",
        "indexes": ["full_name"],
    }
