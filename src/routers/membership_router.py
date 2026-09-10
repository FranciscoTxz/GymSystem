from typing import Annotated

from fastapi import APIRouter, Depends, Query

from common.auth import admin_required
from schemas.admin_schema import AdminInfo
from schemas.membership_schema import Membership, UpdateMembership
from services.membership_service import MembershipService

router = APIRouter(prefix="/membership", tags=["Membership"])

require_max_admin = admin_required({"MAX"})
require_min_admin = admin_required({"MIN", "MAX", "MID"})


@router.get("", status_code=200)
async def get_memberships(
    _: Annotated[AdminInfo, Depends(require_min_admin)],
    next_cursor: str | None = Query(default=None),
    limit: int = Query(default=15, ge=1),
):
    return MembershipService.get_memberships(cursor_id=next_cursor, limit=limit)


@router.get("/info/{membership_id}", status_code=200)
async def get_membership_info(
    membership_id: str,
    _: Annotated[AdminInfo, Depends(require_min_admin)],
):
    return MembershipService.get_membership(membership_id=membership_id)


@router.post("", status_code=201)
async def create_membership(
    payload: Membership, _: Annotated[AdminInfo, Depends(require_max_admin)]
):
    return MembershipService.create_membership(**payload.model_dump())


@router.patch("/info/{membership_id}", status_code=200)
async def update_membership_info(
    membership_id: str,
    payload: UpdateMembership,
    _: Annotated[AdminInfo, Depends(require_max_admin)],
):
    return MembershipService.update_membership(id=membership_id, **payload.model_dump())


@router.delete("/info/{membership_id}", status_code=204)
async def delete_membership(
    membership_id: str, _: Annotated[AdminInfo, Depends(require_max_admin)]
):
    MembershipService.delete_membership(membership_id=membership_id)
