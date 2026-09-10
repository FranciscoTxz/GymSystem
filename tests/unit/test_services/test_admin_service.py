from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

from schemas.admin_schema import AdminType
from services import admin_service as admin_module
from services.admin_service import AdminService


def _admin(**overrides):
    values = {
        "email": "admin@example.com",
        "password_hash": "hash",
        "full_name": "Ada Lovelace",
        "birthdate": date(1990, 1, 1),
        "phone_number": "5551234",
        "type": "MAX",
        "enabled": True,
        "created_at": datetime(2026, 9, 7, tzinfo=UTC),
        "last_login": datetime(2026, 9, 7, tzinfo=UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _stub_admins(monkeypatch, objects):
    monkeypatch.setattr(admin_module, "Admins", SimpleNamespace(objects=objects))


def test_signup_admin_saves_hashed_admin(monkeypatch):
    admin = MagicMock()
    admins = MagicMock(return_value=admin)
    admins.objects.get.side_effect = DoesNotExist
    monkeypatch.setattr(admin_module, "Admins", admins)

    result = AdminService.signup_admin(
        "admin@example.com", "secret", "Ada", "Lovelace", None, None, AdminType.MAX
    )

    assert result == {"message": "Admin registered successfully."}
    assert admins.call_args.kwargs["full_name"] == "Ada Lovelace"
    admin.save.assert_called_once()


def test_signup_admin_rejects_existing_email(monkeypatch):
    admins = MagicMock()
    admins.objects.get.return_value = _admin()
    monkeypatch.setattr(admin_module, "Admins", admins)

    with pytest.raises(HTTPException, match="email already exists") as error:
        AdminService.signup_admin(
            "admin@example.com", "secret", "Ada", "Lovelace", None, None, AdminType.MAX
        )

    assert error.value.status_code == 400


def test_login_admin_returns_token_and_updates_last_login(monkeypatch):
    admin = MagicMock(**vars(_admin(password_hash="expected")))
    objects = MagicMock()
    objects.get.return_value = admin
    _stub_admins(monkeypatch, objects)
    monkeypatch.setattr(
        admin_module,
        "sha1",
        lambda value: SimpleNamespace(hexdigest=lambda: "expected"),
    )
    encode = MagicMock(return_value="jwt-token")
    monkeypatch.setattr(admin_module.jwt, "encode", encode)

    result = AdminService.login_admin("admin@example.com", "secret")

    assert result == {
        "access_token": "jwt-token",
        "admin_name": "Ada Lovelace",
        "role": "MAX",
    }
    admin.save.assert_called_once()
    assert encode.call_args.kwargs["algorithm"] == "HS256"


@pytest.mark.parametrize(
    "admin", [_admin(password_hash="wrong"), _admin(enabled=False)]
)
def test_login_admin_rejects_invalid_credentials(monkeypatch, admin):
    objects = MagicMock()
    objects.get.return_value = admin
    _stub_admins(monkeypatch, objects)
    monkeypatch.setattr(
        admin_module, "sha1", lambda value: SimpleNamespace(hexdigest=lambda: "hash")
    )

    with pytest.raises(HTTPException, match="Invalid email or password") as error:
        AdminService.login_admin("admin@example.com", "secret")

    assert error.value.status_code == 401


def test_login_admin_rejects_unknown_email(monkeypatch):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    _stub_admins(monkeypatch, objects)

    with pytest.raises(HTTPException, match="Invalid email or password"):
        AdminService.login_admin("missing@example.com", "secret")


def test_admin_info_methods_return_schemas(monkeypatch):
    objects = MagicMock()
    objects.get.return_value = _admin()
    _stub_admins(monkeypatch, objects)

    info = AdminService.get_admin_info("admin@example.com")
    full_info = AdminService.get_full_admin_info("admin@example.com")

    assert info.email == "admin@example.com"
    assert full_info.enabled is True
    assert full_info.created_at == datetime(2026, 9, 7, tzinfo=UTC)


@pytest.mark.parametrize(
    "method", [AdminService.get_admin_info, AdminService.get_full_admin_info]
)
def test_admin_info_methods_reject_unknown_email(monkeypatch, method):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    _stub_admins(monkeypatch, objects)

    with pytest.raises(HTTPException, match="Admin profile not found") as error:
        method("missing@example.com")

    assert error.value.status_code == 404


def test_paginate_admins_handles_empty_and_next_page(monkeypatch):
    objects = MagicMock()
    _stub_admins(monkeypatch, objects)
    objects.return_value.order_by.return_value.limit.return_value.only.return_value = []
    assert AdminService._paginate_admins(MagicMock(), 1)["has_next"] is False

    admins = [
        SimpleNamespace(
            email="a@example.com", to_mongo=lambda: {"email": "a@example.com"}
        ),
        SimpleNamespace(
            email="b@example.com", to_mongo=lambda: {"email": "b@example.com"}
        ),
    ]
    objects.return_value.order_by.return_value.limit.return_value.only.return_value = (
        admins
    )
    result = AdminService._paginate_admins(MagicMock(), 1)
    assert result == {
        "items": [{"email": "a@example.com"}],
        "next_cursor": "a@example.com",
        "has_next": True,
    }


def test_get_all_admins_info_uses_name_and_cursor(monkeypatch):
    paginate = MagicMock(return_value={"items": []})
    monkeypatch.setattr(admin_module.AdminService, "_paginate_admins", paginate)

    assert AdminService.get_all_admins_info("Ada", "a@example.com") == {"items": []}
    assert AdminService.get_all_admins_info() == {"items": []}
    assert paginate.call_count == 2


@pytest.mark.parametrize("phone_number,admin_type", [("5550000", "MIN"), (None, None)])
def test_update_admin_info_updates_provided_values(
    monkeypatch, phone_number, admin_type
):
    admin = MagicMock(**vars(_admin()))
    objects = MagicMock()
    objects.get.return_value = admin
    _stub_admins(monkeypatch, objects)

    result = AdminService.update_admin_info(
        "admin@example.com", phone_number, admin_type
    )

    assert result["message"] == "Admin Ada Lovelace information updated successfully."
    assert admin.save.called


def test_update_admin_info_rejects_unknown_admin(monkeypatch):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    _stub_admins(monkeypatch, objects)

    with pytest.raises(HTTPException, match="Admin profile not found"):
        AdminService.update_admin_info("missing@example.com", None, None)


def test_update_admin_password_validates_and_replaces_hash(monkeypatch):
    admin = MagicMock(**vars(_admin(password_hash="old-hash")))
    objects = MagicMock()
    objects.get.return_value = admin
    _stub_admins(monkeypatch, objects)
    monkeypatch.setattr(
        admin_module,
        "sha1",
        lambda value: SimpleNamespace(
            hexdigest=lambda: "old-hash" if b"old" in value else "new-hash"
        ),
    )

    result = AdminService.update_admin_password("admin@example.com", "old", "new")

    assert admin.password_hash == "new-hash"
    assert result["message"] == "Admin Ada Lovelace password updated successfully."


def test_update_admin_password_rejects_invalid_or_unknown_admin(monkeypatch):
    objects = MagicMock()
    objects.get.return_value = _admin(password_hash="wrong")
    _stub_admins(monkeypatch, objects)
    monkeypatch.setattr(
        admin_module, "sha1", lambda value: SimpleNamespace(hexdigest=lambda: "hash")
    )
    with pytest.raises(HTTPException, match="Invalid old password"):
        AdminService.update_admin_password("admin@example.com", "old", "new")

    objects.get.side_effect = DoesNotExist
    with pytest.raises(HTTPException, match="Admin profile not found"):
        AdminService.update_admin_password("missing@example.com", "old", "new")


@pytest.mark.parametrize(
    ("method", "expected_enabled"),
    [(AdminService.deactivate_admin, False), (AdminService.activate_admin, True)],
)
def test_admin_activation_methods_update_status(monkeypatch, method, expected_enabled):
    admin = MagicMock(**vars(_admin()))
    objects = MagicMock()
    objects.get.return_value = admin
    _stub_admins(monkeypatch, objects)

    method("admin@example.com")

    assert admin.enabled is expected_enabled
    admin.save.assert_called_once()


@pytest.mark.parametrize(
    "method",
    [
        AdminService.deactivate_admin,
        AdminService.activate_admin,
        AdminService.delete_admin,
    ],
)
def test_admin_mutation_methods_reject_unknown_admin(monkeypatch, method):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    _stub_admins(monkeypatch, objects)

    with pytest.raises(HTTPException, match="Admin profile not found"):
        method("missing@example.com")


def test_delete_admin_deletes_existing_admin(monkeypatch):
    admin = MagicMock()
    objects = MagicMock()
    objects.get.return_value = admin
    _stub_admins(monkeypatch, objects)

    assert AdminService.delete_admin("admin@example.com") is None
    admin.delete.assert_called_once()
