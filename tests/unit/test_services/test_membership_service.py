from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

from services import membership_service as membership_module
from services.membership_service import MembershipService


def test_get_membership_returns_schema(monkeypatch):
    membership = SimpleNamespace(
        id="premium", days=30, price=500.0, description="Full access"
    )
    objects = MagicMock()
    objects.get.return_value = membership
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    result = MembershipService.get_membership("premium")

    assert result.id == "premium"
    assert result.days == 30
    assert result.price == 500.0
    assert result.description == "Full access"


def test_get_membership_rejects_unknown_id(monkeypatch):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    with pytest.raises(HTTPException, match="Membership not found") as error:
        MembershipService.get_membership("unknown")

    assert error.value.status_code == 404


def test_get_memberships_returns_empty_page(monkeypatch):
    objects = MagicMock()
    objects.return_value.order_by.return_value.limit.return_value = []
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    assert MembershipService.get_memberships() == {
        "items": [],
        "next_cursor": None,
        "has_next": False,
    }


def test_get_memberships_returns_next_cursor(monkeypatch):
    memberships = [
        SimpleNamespace(id="basic", to_mongo=lambda: {"id": "basic"}),
        SimpleNamespace(id="premium", to_mongo=lambda: {"id": "premium"}),
    ]
    objects = MagicMock()
    objects.return_value.order_by.return_value.limit.return_value = memberships
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    result = MembershipService.get_memberships(cursor_id="starter", limit=1)

    assert result == {
        "items": [{"id": "basic"}],
        "next_cursor": "basic",
        "has_next": True,
    }


def test_create_membership_saves_new_membership(monkeypatch):
    new_membership = MagicMock()
    memberships = MagicMock(return_value=new_membership)
    memberships.objects.get.side_effect = DoesNotExist
    monkeypatch.setattr(membership_module, "Memberships", memberships)

    result = MembershipService.create_membership("basic", 30, 300.0, "Gym access")

    assert result == {"message": "Membership created successfully."}
    memberships.assert_called_once_with(
        id="basic", days=30, price=300.0, description="Gym access"
    )
    new_membership.save.assert_called_once()


def test_create_membership_rejects_existing_id(monkeypatch):
    memberships = MagicMock()
    memberships.objects.get.return_value = MagicMock()
    monkeypatch.setattr(membership_module, "Memberships", memberships)

    with pytest.raises(HTTPException, match="Membership already exists") as error:
        MembershipService.create_membership("basic", 30, 300.0)

    assert error.value.status_code == 400


def test_update_membership_updates_all_provided_fields(monkeypatch):
    membership = MagicMock(id="basic", days=30, price=300.0, description="Old")
    objects = MagicMock()
    objects.get.return_value = membership
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    result = MembershipService.update_membership("basic", 60, 550.0, "Updated")

    assert membership.days == 60
    assert membership.price == 550.0
    assert membership.description == "Updated"
    membership.save.assert_called_once()
    assert result["message"] == "basic Membership information updated successfully."


def test_update_membership_saves_without_optional_fields(monkeypatch):
    membership = MagicMock(id="basic")
    objects = MagicMock()
    objects.get.return_value = membership
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    MembershipService.update_membership("basic")

    membership.save.assert_called_once()


def test_update_membership_rejects_unknown_id(monkeypatch):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    with pytest.raises(HTTPException, match="Membership not found") as error:
        MembershipService.update_membership("unknown")

    assert error.value.status_code == 404


def test_delete_membership_deletes_existing_membership(monkeypatch):
    membership = MagicMock()
    objects = MagicMock()
    objects.get.return_value = membership
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    assert MembershipService.delete_membership("basic") is None
    membership.delete.assert_called_once()


def test_delete_membership_rejects_unknown_id(monkeypatch):
    objects = MagicMock()
    objects.get.side_effect = DoesNotExist
    monkeypatch.setattr(
        membership_module, "Memberships", SimpleNamespace(objects=objects)
    )

    with pytest.raises(HTTPException, match="Membership not found") as error:
        MembershipService.delete_membership("unknown")

    assert error.value.status_code == 404
