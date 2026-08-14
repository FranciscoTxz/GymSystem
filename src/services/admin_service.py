from datetime import date, datetime, timedelta
from hashlib import sha1
from zoneinfo import ZoneInfo

import jwt
from fastapi import HTTPException
from mongoengine import DoesNotExist

from common.constants import SECRET_KEY
from models.admins import Admins
from schemas.admin_schema import AdminInfo, AdminInfoFull, AdminType

ADMIN_NOT_FOUND = "Admin profile not found."


class AdminService:
    @staticmethod
    def signup_admin(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        birthdate: date | None,
        phone_number: str | None,
        type: AdminType,
    ):
        try:
            Admins.objects.get(email=email)
            raise HTTPException(
                status_code=400, detail="Invalid input or email already exists"
            )
        except DoesNotExist:
            admin = Admins(
                email=email,
                password_hash=sha1(f"{password}{email}".encode()).hexdigest(),
                first_name=first_name,
                last_name=last_name,
                full_name=f"{first_name} {last_name}",
                birthdate=birthdate,
                phone_number=phone_number,
                type=type,
            )
            admin.save()
            return {"message": "Admin registered successfully."}

    @staticmethod
    def login_admin(email: str, password: str):
        try:
            admin = Admins.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        if (
            admin.password_hash != sha1(f"{password}{email}".encode()).hexdigest()
        ) or not admin.enabled:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        expire = datetime.now(tz=ZoneInfo("America/Mexico_City")) + timedelta(hours=20)

        admin.last_login = datetime.now(tz=ZoneInfo("America/Mexico_City"))
        admin.save()

        token = jwt.encode(
            {
                "email": admin.email,
                "name": admin.full_name,
                "role": admin.type,
                "exp": expire,
            },
            SECRET_KEY,
            algorithm="HS256",
        )
        return {
            "access_token": token,
            "admin_name": f"{admin.full_name}",
            "role": f"{admin.type}",
        }

    @staticmethod
    def get_admin_info(email: str):
        try:
            admin = Admins.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=ADMIN_NOT_FOUND)
        return AdminInfo(
            email=admin.email,
            full_name=admin.full_name,
            birthdate=admin.birthdate,
            phone_number=admin.phone_number,
            type=admin.type,
        )

    @staticmethod
    def get_full_admin_info(email: str):
        try:
            admin = Admins.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=ADMIN_NOT_FOUND)
        return AdminInfoFull(
            email=admin.email,
            full_name=admin.full_name,
            birthdate=admin.birthdate,
            phone_number=admin.phone_number,
            type=admin.type,
            enabled=admin.enabled,
            created_at=admin.created_at,
            last_login=admin.last_login,
        )

    @staticmethod
    def update_admin_info(email: str, phone_number: str | None, type: AdminType | None):
        try:
            admin = Admins.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=ADMIN_NOT_FOUND)

        if phone_number is not None:
            admin.phone_number = phone_number
        if type is not None:
            admin.type = type

        admin.save()
        return {"message": f"Admin {admin.full_name} information updated successfully."}

    @staticmethod
    def update_admin_password(email: str, old_password: str, new_password: str):
        try:
            admin = Admins.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=ADMIN_NOT_FOUND)

        if admin.password_hash != sha1(f"{old_password}{email}".encode()).hexdigest():
            raise HTTPException(status_code=400, detail="Invalid old password")

        admin.password_hash = sha1(f"{new_password}{email}".encode()).hexdigest()
        admin.save()
        return {"message": f"Admin {admin.full_name} password updated successfully."}

    @staticmethod
    def deactivate_admin(email: str):
        try:
            admin = Admins.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=ADMIN_NOT_FOUND)

        admin.enabled = False
        admin.save()

    @staticmethod
    def activate_admin(email: str):
        try:
            admin = Admins.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=ADMIN_NOT_FOUND)

        admin.enabled = True
        admin.save()
        return {"message": f"Admin {admin.full_name} account activated successfully."}

    @staticmethod
    def delete_admin(email: str):
        try:
            admin = Admins.objects.get(email=email)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=ADMIN_NOT_FOUND)

        admin.delete()
