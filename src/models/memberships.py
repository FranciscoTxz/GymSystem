from typing import ClassVar

from mongoengine import Document, FloatField, IntField, StringField


class Memberships(Document):
    id = StringField(primary_key=True, required=True)
    days = IntField(required=True)
    price = FloatField(required=True)
    description = StringField(required=False, default="None")

    meta: ClassVar[dict[str, object]] = {"collection": "memberships"}
