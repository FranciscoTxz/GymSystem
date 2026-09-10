from datetime import datetime
from typing import ClassVar
from zoneinfo import ZoneInfo

from mongoengine import Document, FloatField, IntField, StringField


class Statistics(Document):
    id = StringField(primary_key=True, required=True)
    year = IntField(required=True)
    month = IntField(required=True)
    membership = StringField(required=True)
    sold_memberships = IntField(required=True, default=0)
    amount = FloatField(required=True, default=0)

    meta: ClassVar[dict[str, object]] = {
        "collection": "statistics",
        "indexes": ["year", "month", "membership"],
    }

    @staticmethod
    def current_year_month() -> tuple[int, int]:
        today = datetime.now(tz=ZoneInfo("America/Mexico_City"))
        return today.year, today.month

    @staticmethod
    def build_id(year: int, month: int, membership: str) -> str:
        return f"{year}-{month:02d}-{membership}"

    @classmethod
    def current_month_id(cls, membership: str) -> str:
        year, month = cls.current_year_month()
        return cls.build_id(year=year, month=month, membership=membership)
