from typing import Annotated

from fastapi import APIRouter, Depends

from common.auth import admin_required
from schemas.admin_schema import AdminInfo, LogInAdmin, SignUpAdmin
from services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])

require_max_admin = admin_required({"MAX"})


@router.post("/sign-up", status_code=201)
async def sign_up_admin(payload: SignUpAdmin):
    result = AdminService.signup_admin(**payload.model_dump())
    return result


@router.post("/sign-in", status_code=200)
async def sign_in_admin(payload: LogInAdmin):
    result = AdminService.login_admin(email=payload.email, password=payload.password)
    return result


@router.get("/info/{email}", status_code=200)
async def get_admin_info(
    email: str, x: Annotated[AdminInfo, Depends(require_max_admin)]
):
    result = AdminService.get_admin_info(email)
    return result
