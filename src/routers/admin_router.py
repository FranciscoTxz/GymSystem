from fastapi import APIRouter

from schemas.admin_schema import LogInAdmin, SignUpAdmin
from services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/sign-up", status_code=201)
async def sign_up_admin(payload: SignUpAdmin):
    result = AdminService.signup_admin(**payload.model_dump())
    return result


@router.post("/sign-in", status_code=200)
async def sign_in_admin(payload: LogInAdmin):
    result = AdminService.login_admin(email=payload.email, password=payload.password)
    return result
