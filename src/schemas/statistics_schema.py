from pydantic import BaseModel


class StatisticInfo(BaseModel):
    id: str
    year: int
    month: int
    membership: str
    sold_memberships: int
    amount: float
