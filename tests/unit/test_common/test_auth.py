from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from common import auth as auth_module


def test_admin_required_returns_admin_for_valid_authorized_token(monkeypatch):
    admin_info = SimpleNamespace(enabled=True, type="MAX")
    monkeypatch.setattr(
        auth_module.jwt,
        "decode",
        lambda *args, **kwargs: {"email": "admin@example.com"},
    )
    monkeypatch.setattr(
        auth_module.AdminService,
        "get_full_admin_info",
        lambda email: admin_info,
    )

    result = auth_module.admin_required({"MAX"})("Bearer token")

    assert result is admin_info


def test_admin_required_rejects_token_without_email(monkeypatch):
    monkeypatch.setattr(auth_module.jwt, "decode", lambda *args, **kwargs: {})

    with pytest.raises(HTTPException, match="Missing or invalid token") as error:
        auth_module.admin_required()("Bearer token")

    assert error.value.status_code == 401


def test_admin_required_rejects_disabled_admin(monkeypatch):
    monkeypatch.setattr(
        auth_module.jwt,
        "decode",
        lambda *args, **kwargs: {"email": "admin@example.com"},
    )
    monkeypatch.setattr(
        auth_module.AdminService,
        "get_full_admin_info",
        lambda email: SimpleNamespace(enabled=False, type="MAX"),
    )

    with pytest.raises(HTTPException, match="Admin account is disabled") as error:
        auth_module.admin_required()("Bearer token")

    assert error.value.status_code == 403


def test_admin_required_rejects_unauthorized_admin_type(monkeypatch):
    monkeypatch.setattr(
        auth_module.jwt,
        "decode",
        lambda *args, **kwargs: {"email": "admin@example.com"},
    )
    monkeypatch.setattr(
        auth_module.AdminService,
        "get_full_admin_info",
        lambda email: SimpleNamespace(enabled=True, type="MIN"),
    )

    with pytest.raises(HTTPException, match="Unauthorized request") as error:
        auth_module.admin_required({"MAX"})("Bearer token")

    assert error.value.status_code == 403


def test_admin_required_rejects_expired_token(monkeypatch):
    def raise_expired_token(*args, **kwargs):
        raise auth_module.jwt.ExpiredSignatureError()

    monkeypatch.setattr(auth_module.jwt, "decode", raise_expired_token)

    with pytest.raises(HTTPException, match="Token has expired") as error:
        auth_module.admin_required()("Bearer token")

    assert error.value.status_code == 401


def test_admin_required_rejects_invalid_token(monkeypatch):
    def raise_invalid_token(*args, **kwargs):
        raise auth_module.jwt.InvalidTokenError()

    monkeypatch.setattr(auth_module.jwt, "decode", raise_invalid_token)

    with pytest.raises(HTTPException, match="Invalid token") as error:
        auth_module.admin_required()("Bearer token")

    assert error.value.status_code == 401


def test_admin_required_preserves_http_exceptions(monkeypatch):
    def raise_http_exception(*args, **kwargs):
        raise HTTPException(status_code=418, detail="Expected error")

    monkeypatch.setattr(auth_module.jwt, "decode", raise_http_exception)

    with pytest.raises(HTTPException, match="Expected error") as error:
        auth_module.admin_required()("Bearer token")

    assert error.value.status_code == 418


def test_admin_required_hides_unexpected_errors(monkeypatch):
    def raise_unexpected_error(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(auth_module.jwt, "decode", raise_unexpected_error)

    with pytest.raises(HTTPException, match="Missing or invalid token") as error:
        auth_module.admin_required()("Bearer token")

    assert error.value.status_code == 401
