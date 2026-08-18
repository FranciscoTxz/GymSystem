from typing import Annotated

from fastapi import APIRouter, Depends, Query

from common.auth import admin_required
from schemas.admin_schema import (
    AdminInfo,
    AdminPasswordUpdate,
    LogInAdmin,
    SignUpAdmin,
    UpdateAdmin,
)
from services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])

require_max_admin = admin_required({"MAX"})
require_min_admin = admin_required({"MIN", "MAX", "MID"})


@router.get("", status_code=200)
def get_all_admins(
    _: Annotated[AdminInfo, Depends(require_max_admin)],
    next_cursor: str | None = Query(default=None),
    limit: int = Query(default=15, ge=1),
    name: str | None = Query(default=None),
):
    return AdminService.get_all_admins_info(
        name=name, cursor_id=next_cursor, limit=limit
    )


@router.post("/sign-up", status_code=201)
async def sign_up_admin(
    payload: SignUpAdmin,
    _: Annotated[AdminInfo, Depends(require_max_admin)],
):
    return AdminService.signup_admin(**payload.model_dump())


@router.post("/sign-in", status_code=200)
async def sign_in_admin(payload: LogInAdmin):
    return AdminService.login_admin(email=payload.email, password=payload.password)


@router.get("/info", status_code=200)
async def get_admin_info_simple(
    admin_info: Annotated[AdminInfo, Depends(require_min_admin)],
):
    return AdminService.get_admin_info(admin_info.email)


@router.get("/info/{email}", status_code=200)
async def get_admin_info(
    email: str, _: Annotated[AdminInfo, Depends(require_max_admin)]
):
    return AdminService.get_full_admin_info(email)


@router.patch("/info", status_code=200)
async def update_admin_info(
    payload: UpdateAdmin, admin_info: Annotated[AdminInfo, Depends(require_max_admin)]
):
    if not payload.email:
        payload.email = admin_info.email
    return AdminService.update_admin_info(
        email=payload.email,
        phone_number=payload.phone_number,
        type=payload.type,
    )


@router.patch("/password", status_code=200)
async def update_admin_password(
    payload: AdminPasswordUpdate,
    admin_info: Annotated[AdminInfo, Depends(require_min_admin)],
):
    return AdminService.update_admin_password(
        email=admin_info.email,
        old_password=payload.old_password,
        new_password=payload.new_password,
    )


@router.delete("/deactivate/{email}", status_code=204)
async def deactivate_admin(
    email: str, _: Annotated[AdminInfo, Depends(require_max_admin)]
):
    return AdminService.deactivate_admin(email)


@router.patch("/activate/{email}", status_code=200)
async def activate_admin(
    email: str, _: Annotated[AdminInfo, Depends(require_max_admin)]
):
    return AdminService.activate_admin(email)


@router.delete("/delete/{email}", status_code=204)
async def delete_admin(email: str, _: Annotated[AdminInfo, Depends(require_max_admin)]):
    return AdminService.delete_admin(email)
