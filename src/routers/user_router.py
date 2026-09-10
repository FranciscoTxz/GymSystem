from typing import Annotated

from fastapi import APIRouter, Depends, Query

from common.auth import admin_required
from schemas.admin_schema import AdminInfo
from schemas.user_schema import CreateUser, UpdateMembershipUser, UpdateUser
from services.user_service import UserService

router = APIRouter(prefix="/user", tags=["User"])

require_min_admin = admin_required({"MIN", "MAX", "MID"})


@router.get("", status_code=200)
async def get_all_users(
    _: Annotated[AdminInfo, Depends(require_min_admin)],
    next_cursor: str | None = Query(default=None),
    limit: int = Query(default=15, ge=1),
    name: str | None = Query(default=None),
):
    return UserService.get_all_users_info(name=name, cursor_id=next_cursor, limit=limit)


@router.get("/access/{id}", status_code=200)
async def get_user_access(id: int, _: Annotated[AdminInfo, Depends(require_min_admin)]):
    return UserService.get_user_access(id)


@router.post("", status_code=201)
async def create_user(
    payload: CreateUser, _: Annotated[AdminInfo, Depends(require_min_admin)]
):
    return UserService.create_user(**payload.model_dump())


@router.get("/info/{id}", status_code=200)
async def get_user_info(id: int, _: Annotated[AdminInfo, Depends(require_min_admin)]):
    return UserService.get_user_info(id)


@router.get("/info/{id}/full", status_code=200)
async def get_full_user_info(
    id: int, _: Annotated[AdminInfo, Depends(require_min_admin)]
):
    return UserService.get_full_user_info(id)


@router.patch("/info/{id}", status_code=200)
async def update_user_info(
    id: int, payload: UpdateUser, _: Annotated[AdminInfo, Depends(require_min_admin)]
):
    return UserService.update_user_info(id=id, **payload.model_dump())


@router.patch("/membership/{id}", status_code=200)
async def update_user_membership(
    id: int,
    payload: UpdateMembershipUser,
    _: Annotated[AdminInfo, Depends(require_min_admin)],
):
    return UserService.update_user_membership(id=id, membership=payload.membership)


@router.patch("/deactivate/{id}", status_code=200)
async def deactivate_user(id: int, _: Annotated[AdminInfo, Depends(require_min_admin)]):
    return UserService.deactivate_user(id)


@router.patch("/activate/{id}", status_code=200)
async def activate_user(id: int, _: Annotated[AdminInfo, Depends(require_min_admin)]):
    return UserService.activate_user(id)


@router.patch("/ban/{id}", status_code=200)
async def ban_user(id: int, _: Annotated[AdminInfo, Depends(require_min_admin)]):
    return UserService.ban_user(id)


@router.delete("/delete/{id}", status_code=204)
async def delete_user(id: int, _: Annotated[AdminInfo, Depends(require_min_admin)]):
    return UserService.delete_user(id)
