from fastapi import HTTPException
from mongoengine import DoesNotExist, Q

from models.memberships import Memberships
from schemas.membership_schema import Membership

MEMBERSHIP_NOT_FOUND = "Membership not found."


class MembershipService:
    @staticmethod
    def get_membership(
        membership_id: str | None = None,
    ):
        try:
            membership = Memberships.objects.get(id=membership_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=MEMBERSHIP_NOT_FOUND)
        return Membership(
            id=membership.id,
            days=membership.days,
            price=membership.price,
            description=membership.description,
        )

    @staticmethod
    def get_memberships(cursor_id: str | None = None, limit: int = 15):
        query = Q()

        if cursor_id:
            query &= Q(id__gt=cursor_id)

        items = list(Memberships.objects(query).order_by("id").limit(limit + 1))

        if not items:
            return {
                "items": [],
                "next_cursor": None,
                "has_next": False,
            }

        has_next = len(items) > limit
        page_items = items[:limit]
        next_cursor = page_items[-1].id if has_next and page_items else None

        items = [item.to_mongo() for item in page_items]

        return {
            "items": items,
            "next_cursor": str(next_cursor) if next_cursor else None,
            "has_next": has_next,
        }

    @staticmethod
    def create_membership(
        id: str, days: int, price: float, description: str | None = None
    ):
        try:
            Memberships.objects.get(id=id)
            raise HTTPException(status_code=400, detail="Membership already exists")
        except DoesNotExist:
            membership = Memberships(
                id=id, days=days, price=price, description=description
            )
            membership.save()
            return {"message": "Membership created successfully."}

    @staticmethod
    def update_membership(
        id: str,
        days: int | None = None,
        price: float | None = None,
        description: str | None = None,
    ):
        try:
            membership = Memberships.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=MEMBERSHIP_NOT_FOUND)

        if days is not None:
            membership.days = days

        if price is not None:
            membership.price = price

        if description is not None:
            membership.description = description

        membership.save()
        return {
            "message": f"{membership.id} Membership information updated successfully."
        }

    @staticmethod
    def delete_membership(membership_id: str):
        try:
            membership = Memberships.objects.get(id=membership_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=MEMBERSHIP_NOT_FOUND)

        membership.delete()
