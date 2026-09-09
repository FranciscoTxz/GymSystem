import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("GymSystem")
_access_token: str | None = None


def _api_url() -> str:
    return os.getenv("MCP_API_URL", "http://127.0.0.1:8080").rstrip("/")


async def _get_access_token(client: httpx.AsyncClient) -> str:
    global _access_token
    if _access_token:
        return _access_token

    email = os.getenv("MCP_ADMIN_EMAIL") or os.getenv("MCP_ADMIN")
    password = os.getenv("MCP_ADMIN_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "MCP_ADMIN or MCP_ADMIN_EMAIL and MCP_ADMIN_PASSWORD must be configured"
        )

    response = await client.post(
        "/admin/sign-in", json={"email": email, "password": password}
    )
    if response.is_error:
        raise RuntimeError(f"Admin sign-in failed ({response.status_code})")

    _access_token = response.json()["access_token"]
    if not _access_token:
        raise RuntimeError("Failed to obtain access token")
    return _access_token


async def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    filtered_params = (
        {key: value for key, value in params.items() if value is not None}
        if params
        else None
    )
    async with httpx.AsyncClient(base_url=_api_url(), timeout=20.0) as client:
        global _access_token
        response: httpx.Response | None = None
        for attempt in range(2):
            response = await client.request(
                method,
                path,
                headers={"Authorization": await _get_access_token(client)},
                params=filtered_params,
                json=payload,
            )
            if response.status_code != 401 or attempt == 1:
                break
            _access_token = None
        assert response is not None
        if response.is_error:
            detail: Any
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise RuntimeError(f"API {response.status_code}: {detail}")
        if response.status_code == 204 or not response.content:
            return {"ok": True}
        return response.json()


@mcp.tool()
async def list_users(
    name: str | None = None,
    next_cursor: str | None = None,
    limit: int = 15,
) -> Any:
    """List gym users, optionally filtered by name."""
    return await _request(
        "GET",
        "/user",
        params={"name": name, "next_cursor": next_cursor, "limit": limit},
    )


@mcp.tool()
async def get_user(user_id: int, full: bool = False) -> Any:
    """Get the basic or complete information for a user."""
    path = f"/user/info/{user_id}/full" if full else f"/user/info/{user_id}"
    return await _request("GET", path)


@mcp.tool()
async def create_user(
    membership: str,
    first_name: str,
    last_name: str,
    birthdate: str,
    phone_number: str,
    emergency_contact: str,
    email: str | None = None,
    photo_url: str | None = None,
) -> Any:
    """Create a user. birthdate must use the YYYY-MM-DD format."""
    payload = {
        "membership": membership,
        "first_name": first_name,
        "last_name": last_name,
        "birthdate": birthdate,
        "phone_number": phone_number,
        "emergency_contact": emergency_contact,
        "email": email,
        "photo_url": photo_url,
    }
    return await _request("POST", "/user", payload=payload)


@mcp.tool()
async def set_user_state(user_id: int, state: str) -> Any:
    """Activate or deactivate a user. state must be ACTIVE or DEACTIVATED."""
    paths = {
        "ACTIVE": f"/user/activate/{user_id}",
        "DEACTIVATED": f"/user/deactivate/{user_id}",
    }
    try:
        path = paths[state.upper()]
    except KeyError as error:
        raise ValueError("state must be ACTIVE or DEACTIVATED") from error
    return await _request("PATCH", path)


@mcp.tool()
async def list_memberships(next_cursor: str | None = None, limit: int = 15) -> Any:
    """List the available memberships."""
    return await _request(
        "GET", "/membership", params={"next_cursor": next_cursor, "limit": limit}
    )


@mcp.tool()
async def get_statistics(
    year: int | None = None,
    month: int | None = None,
    membership: str | None = None,
) -> Any:
    """Get gym statistics for an optional period."""
    return await _request(
        "GET",
        "/statistics",
        params={"year": year, "month": month, "membership": membership},
    )


@mcp.tool()
async def get_current_month_statistics(membership: str | None = None) -> Any:
    """Get statistics for the current month."""
    return await _request(
        "GET", "/statistics/current", params={"membership": membership}
    )


if __name__ == "__main__":
    mcp.run()
