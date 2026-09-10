from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

from services import user_service as user_module
from services.user_service import UserService

TODAY = datetime.now(tz=ZoneInfo("America/Mexico_City")).date()


def _user(**changes):
    values = {
        "id": 1,
        "membership": "basic",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "full_name": "Ada Lovelace",
        "birthdate": "1990-01-01",
        "phone_number": "555",
        "email": "ada@example.com",
        "emergency_contact": "Grace",
        "photo_url": None,
        "state": user_module.UserState.active,
        "fingerprint_template": None,
        "last_visit": datetime(2026, 9, 1, tzinfo=UTC),
        "next_payment": TODAY + timedelta(days=5),
        "enabled": True,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(changes)
    return MagicMock(**values)


def _users(monkeypatch, objects):
    monkeypatch.setattr(user_module, "Users", SimpleNamespace(objects=objects))


def test_next_id_handles_first_and_following_user(monkeypatch):
    objects = MagicMock()
    objects.order_by.return_value.first.side_effect = [None, SimpleNamespace(id=4)]
    _users(monkeypatch, objects)
    assert UserService._next_id() == 1
    assert UserService._next_id() == 5


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"next_payment": TODAY}, "expired"),
        ({"state": user_module.UserState.banned}, "banned"),
        ({"state": user_module.UserState.deactivated}, "deactivated"),
        ({"enabled": False}, "disabled"),
    ],
)
def test_get_user_access_rejects_invalid_status(monkeypatch, changes, message):
    objects = MagicMock()
    objects.get.return_value = _user(**changes)
    _users(monkeypatch, objects)
    with pytest.raises(HTTPException, match=message):
        UserService.get_user_access(1)


def test_get_user_access_updates_active_user(monkeypatch):
    user = _user()
    objects = MagicMock()
    objects.get.return_value = user
    _users(monkeypatch, objects)
    result = UserService.get_user_access(1)
    assert result["remaining_days"] == 5
    user.save.assert_called_once()


def test_get_user_access_allows_non_active_valid_user_without_visit(monkeypatch):
    user = _user(state="pending")
    objects = MagicMock()
    objects.get.return_value = user
    _users(monkeypatch, objects)
    assert UserService.get_user_access(1)["remaining_days"] == 5
    user.save.assert_not_called()


@pytest.mark.parametrize(
    "method",
    [
        UserService.get_user_access,
        UserService.get_user_info,
        UserService.get_full_user_info,
        UserService.update_user_info,
        UserService.update_user_membership,
        UserService.deactivate_user,
        UserService.activate_user,
        UserService.ban_user,
        UserService.delete_user,
    ],
)
def test_user_methods_reject_unknown_user(monkeypatch, method):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    _users(monkeypatch, objects)
    arguments = (
        (1, None, None, None, None)
        if method is UserService.update_user_info
        else (1, "basic")
        if method is UserService.update_user_membership
        else (1,)
    )
    with pytest.raises(HTTPException, match="User not found"):
        method(*arguments)


def test_create_user_saves_and_records_sale(monkeypatch):
    user = MagicMock(id=8)
    users = MagicMock(return_value=user)
    monkeypatch.setattr(user_module, "Users", users)
    membership = SimpleNamespace(days=30, price=300.0)
    monkeypatch.setattr(
        user_module,
        "Memberships",
        SimpleNamespace(objects=SimpleNamespace(get=lambda **kwargs: membership)),
    )
    monkeypatch.setattr(UserService, "_next_id", lambda: 8)
    sale = MagicMock()
    monkeypatch.setattr(user_module.StatisticsService, "add_membership_sale", sale)
    assert (
        UserService.create_user(
            "basic",
            "Ada",
            "Lovelace",
            date(1990, 1, 1),
            "555",
            None,
            "Grace",
            None,
            None,
        )["user_id"]
        == 8
    )
    user.save.assert_called_once()
    sale.assert_called_once_with(membership="basic", amount=300.0)


def test_create_user_rejects_unknown_membership(monkeypatch):
    monkeypatch.setattr(
        user_module,
        "Memberships",
        SimpleNamespace(
            objects=SimpleNamespace(get=MagicMock(side_effect=DoesNotExist))
        ),
    )
    with pytest.raises(HTTPException, match="Membership not found"):
        UserService.create_user("bad", "A", "B", TODAY, "1", None, "C", None, None)


def test_user_info_methods_return_schemas(monkeypatch):
    objects = MagicMock()
    objects.get.return_value = _user()
    _users(monkeypatch, objects)
    assert UserService.get_user_info(1).full_name == "Ada Lovelace"
    assert UserService.get_full_user_info(1).enabled is True


def test_paginate_and_search_users(monkeypatch):
    objects = MagicMock()
    objects.return_value.order_by.return_value.limit.return_value.only.return_value.as_pymongo.return_value = []
    _users(monkeypatch, objects)
    assert UserService._paginate_users(MagicMock(), 1)["items"] == []
    objects.return_value.order_by.return_value.limit.return_value.only.return_value.as_pymongo.return_value = [
        {"_id": 1},
        {"_id": 2},
    ]
    assert UserService._paginate_users(MagicMock(), 1) == {
        "items": [{"_id": 1}],
        "next_cursor": "1",
        "has_next": True,
    }
    paginate = MagicMock(return_value={"items": []})
    monkeypatch.setattr(UserService, "_paginate_users", paginate)
    UserService.get_all_users_info("Ada", "1")
    UserService.get_all_users_info()
    assert paginate.call_count == 2


def test_update_user_info_updates_all_optional_fields(monkeypatch):
    user = _user()
    objects = MagicMock()
    objects.get.return_value = user
    _users(monkeypatch, objects)
    UserService.update_user_info(
        1, "2", "new@example.com", "New", "https://example.com/a.jpg"
    )
    assert user.phone_number == "2" and user.email == "new@example.com"
    user.save.assert_called_once()


def test_update_user_info_saves_without_optional_fields(monkeypatch):
    user = _user()
    objects = MagicMock()
    objects.get.return_value = user
    _users(monkeypatch, objects)
    UserService.update_user_info(1, None, None, None, None)
    user.save.assert_called_once()


def test_update_membership_and_account_mutations(monkeypatch):
    user = _user()
    objects = MagicMock()
    objects.get.return_value = user
    _users(monkeypatch, objects)
    plan = SimpleNamespace(days=30, price=300.0)
    monkeypatch.setattr(
        user_module,
        "Memberships",
        SimpleNamespace(objects=SimpleNamespace(get=lambda **kwargs: plan)),
    )
    sale = MagicMock()
    monkeypatch.setattr(user_module.StatisticsService, "add_membership_sale", sale)
    UserService.update_user_membership(1, "premium")
    assert user.membership == "premium"
    sale.assert_called_once()
    UserService.deactivate_user(1)
    assert user.enabled is False
    UserService.activate_user(1)
    assert user.enabled is True
    UserService.ban_user(1)
    assert user.state == user_module.UserState.banned
    UserService.delete_user(1)
    user.delete.assert_called_once()


def test_update_membership_rejects_unknown_plan(monkeypatch):
    objects = MagicMock()
    objects.get.return_value = _user()
    _users(monkeypatch, objects)
    monkeypatch.setattr(
        user_module,
        "Memberships",
        SimpleNamespace(
            objects=SimpleNamespace(get=MagicMock(side_effect=DoesNotExist))
        ),
    )
    with pytest.raises(HTTPException, match="Membership not found"):
        UserService.update_user_membership(1, "bad")
