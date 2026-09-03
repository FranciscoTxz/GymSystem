from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from mongoengine import DoesNotExist, Q

from models.memberships import Memberships
from models.users import Users
from schemas.user_schema import UserInfo, UserInfoFull, UserState
from services.statistics_service import StatisticsService

USER_NOT_FOUND = "User not found."
MEMBERSHIP_NOT_FOUND = "Membership not found."


class UserService:
    @staticmethod
    def _next_id() -> int:
        last_user = Users.objects.order_by("-id").first()
        return (last_user.id + 1) if last_user else 1

    @staticmethod
    def get_user_access(id: int):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        if user.next_payment <= datetime.now(tz=ZoneInfo("America/Mexico_City")).date():
            raise HTTPException(
                status_code=403, detail="User account has expired membership."
            )

        if user.state == UserState.banned:
            raise HTTPException(status_code=403, detail="User account is banned.")

        if user.state == UserState.deactivated:
            raise HTTPException(status_code=403, detail="User account is deactivated.")

        if user.enabled is False:
            raise HTTPException(status_code=403, detail="User account is disabled.")

        if user.state == UserState.active:
            user.last_visit = datetime.now(tz=ZoneInfo("America/Mexico_City"))
            user.save()

        return {
            "message": f"Welcome {user.full_name}! Access granted.",
            "remaining_days": (
                user.next_payment
                - datetime.now(tz=ZoneInfo("America/Mexico_City")).date()
            ).days,
        }

    @staticmethod
    def create_user(
        membership: str,
        first_name: str,
        last_name: str,
        birthdate: date,
        phone_number: str,
        email: str | None,
        emergency_contact: str,
        photo_url: str | None,
        fingerprint_template: bytes | None,
    ):
        try:
            membership_plan = Memberships.objects.get(id=membership)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=MEMBERSHIP_NOT_FOUND)

        today = datetime.now(tz=ZoneInfo("America/Mexico_City")).date()
        user = Users(
            id=UserService._next_id(),
            membership=membership,
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            birthdate=birthdate.isoformat(),
            phone_number=phone_number,
            email=email,
            emergency_contact=emergency_contact,
            photo_url=photo_url,
            fingerprint_template=fingerprint_template,
            next_payment=today + timedelta(days=membership_plan.days),
        )
        user.save()
        StatisticsService.add_membership_sale(
            membership=membership,
            amount=membership_plan.price,
        )
        return {"message": "User registered successfully.", "user_id": user.id}

    @staticmethod
    def get_user_info(id: int):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)
        return UserInfo(
            id=user.id,
            membership=user.membership,
            full_name=user.full_name,
            birthdate=user.birthdate,
            phone_number=user.phone_number,
            photo_url=user.photo_url,
            state=user.state,
        )

    @staticmethod
    def get_full_user_info(id: int):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)
        return UserInfoFull(
            id=user.id,
            membership=user.membership,
            full_name=user.full_name,
            first_name=user.first_name,
            last_name=user.last_name,
            birthdate=user.birthdate,
            phone_number=user.phone_number,
            email=user.email,
            emergency_contact=user.emergency_contact,
            photo_url=user.photo_url,
            state=user.state,
            fingerprint_template=user.fingerprint_template,
            last_visit=user.last_visit,
            next_payment=user.next_payment,
            enabled=user.enabled,
            created_at=user.created_at,
        )

    @staticmethod
    def _paginate_users(query, limit: int):
        items = list(
            Users.objects(query)
            .order_by("id")
            .limit(limit + 1)
            .only("id", "full_name", "membership", "state", "next_payment")
            .as_pymongo()
        )

        if not items:
            return {
                "items": [],
                "next_cursor": None,
                "has_next": False,
            }

        has_next = len(items) > limit
        page_items = items[:limit]
        next_cursor = page_items[-1]["_id"] if has_next and page_items else None

        return {
            "items": page_items,
            "next_cursor": str(next_cursor) if next_cursor else None,
            "has_next": has_next,
        }

    @staticmethod
    def get_all_users_info(
        name: str | None = None, cursor_id: str | None = None, limit: int = 15
    ):
        if name:
            query = Q(full_name__icontains=name)
        else:
            query = Q()

        if cursor_id:
            query &= Q(id__gt=int(cursor_id))

        return UserService._paginate_users(query, limit)

    @staticmethod
    def update_user_info(
        id: int,
        phone_number: str | None,
        email: str | None,
        emergency_contact: str | None,
        photo_url: str | None,
    ):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        if phone_number is not None:
            user.phone_number = phone_number
        if email is not None:
            user.email = email
        if emergency_contact is not None:
            user.emergency_contact = emergency_contact
        if photo_url is not None:
            user.photo_url = photo_url

        user.save()
        return {"message": f"User {user.full_name} information updated successfully."}

    @staticmethod
    def update_user_membership(id: int, membership: str):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        try:
            membership_plan = Memberships.objects.get(id=membership)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=MEMBERSHIP_NOT_FOUND)

        today = datetime.now(tz=ZoneInfo("America/Mexico_City")).date()
        start_date = max(today, user.next_payment)

        user.membership = membership
        user.next_payment = start_date + timedelta(days=membership_plan.days)
        user.save()
        StatisticsService.add_membership_sale(
            membership=membership,
            amount=membership_plan.price,
        )
        return {"message": f"User {user.full_name} membership updated successfully."}

    @staticmethod
    def deactivate_user(id: int):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        user.state = UserState.deactivated
        user.enabled = False
        user.save()
        return {"message": f"User {user.full_name} account deactivated successfully."}

    @staticmethod
    def activate_user(id: int):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        user.state = UserState.active
        user.enabled = True
        user.save()
        return {"message": f"User {user.full_name} account activated successfully."}

    @staticmethod
    def ban_user(id: int):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        user.state = UserState.banned
        user.enabled = False
        user.save()
        return {"message": f"User {user.full_name} has been banned."}

    @staticmethod
    def delete_user(id: int):
        try:
            user = Users.objects.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND)

        user.delete()
