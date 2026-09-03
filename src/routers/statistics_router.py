from typing import Annotated

from fastapi import APIRouter, Depends, Query

from common.auth import admin_required
from schemas.admin_schema import AdminInfo
from services.statistics_service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["Statistics"])

require_max_admin = admin_required({"MAX"})


@router.get("", status_code=200)
async def get_statistics(
    _: Annotated[AdminInfo, Depends(require_max_admin)],
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    membership: str | None = Query(default=None),
):
    return StatisticsService.get_all_statistics(
        year=year, month=month, membership=membership
    )


@router.get("/current", status_code=200)
async def get_current_month_statistics(
    _: Annotated[AdminInfo, Depends(require_max_admin)],
    membership: str | None = Query(default=None),
):
    return StatisticsService.get_current_month(membership=membership)
