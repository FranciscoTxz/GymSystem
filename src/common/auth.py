import jwt
from fastapi import Header, HTTPException

from common.constants import SECRET_KEY
from schemas.admin_schema import AdminInfo
from services.admin_service import AdminService


def admin_required(types: set[str] | None = None):
    """Dependency that validates JWT token and checks admin role."""

    def verify_token(authorization: str = Header(None)) -> AdminInfo:
        try:
            attributes = jwt.decode(authorization, SECRET_KEY, algorithms=["HS256"])
            email = attributes.get("email")

            if not email:
                raise HTTPException(
                    status_code=401, detail="Unauthorized: Missing or invalid token"
                )

            admin_info = AdminService.get_full_admin_info(email)

            if not admin_info.enabled:
                raise HTTPException(
                    status_code=403, detail="Forbidden: Admin account is disabled"
                )

            if types and admin_info.type.upper() not in types:
                raise HTTPException(
                    status_code=403, detail="Forbidden: Unauthorized request"
                )

            return admin_info

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401, detail="Unauthorized: Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")
        except HTTPException:
            raise
        except Exception:  # noqa: BLE001 - catch-all guard, always returns 401
            raise HTTPException(
                status_code=401, detail="Unauthorized: Missing or invalid token"
            )

    return verify_token


# TODO for users
# def role_required_services(types: set[str]):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(admin_info: AdminInfo, *args, **kwargs):
#             admin_role = admin_info.type
#             if admin_role.upper() not in types:
#                 return 403, {"status": "Forbidden: Unauthorized request"}
#             return func(admin_info, *args, **kwargs)
#         return wrapper
#     return decorator
