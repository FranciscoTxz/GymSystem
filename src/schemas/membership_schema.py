from pydantic import BaseModel, Field


class Membership(BaseModel):
    id: str = Field(min_length=3, max_length=20)
    days: int = Field(ge=1)
    price: float = Field(ge=1)
    description: str
