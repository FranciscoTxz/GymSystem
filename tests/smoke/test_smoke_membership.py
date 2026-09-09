from uuid import uuid4

import pytest

MEMBERSHIP_NOT_FOUND = "Membership not found."


@pytest.fixture(scope="function")
def create_membership(admin_max_client):
    membership_id = f"m{uuid4().hex[:8]}"
    response = admin_max_client.post(
        "/membership",
        json={
            "id": membership_id,
            "days": 30,
            "price": 99.99,
            "description": "Test membership for smoke suite",
        },
    )

    assert response.status_code == 201, f"Membership creation failed: {response.json()}"
    assert response.json().get("message") == "Membership created successfully."

    return {
        "id": membership_id,
        "days": 30,
        "price": 99.99,
        "description": "Test membership for smoke suite",
    }


def test_get_all_memberships_success(admin_min_client):
    response = admin_min_client.get(
        "/membership", params={"next_cursor": None, "limit": 10}
    )

    assert response.status_code == 200, (
        f"Failed to get all memberships: {response.json()}"
    )
    assert isinstance(response.json().get("items"), list), (
        "Expected a list of memberships"
    )


def test_get_membership_info_success(admin_min_client):
    response = admin_min_client.get("/membership/info/weekly")

    assert response.status_code == 200, (
        f"Failed to get membership info: {response.json()}"
    )
    assert isinstance(response.json(), dict), (
        "Expected a dictionary with membership info"
    )
    assert response.json().get("id") == "weekly"
    assert response.json().get("days") == 7


def test_get_membership_info_not_found(admin_max_client):
    response = admin_max_client.get(f"/membership/info/membership{uuid4().hex}")

    assert response.status_code == 404
    assert response.json().get("message") == MEMBERSHIP_NOT_FOUND


def test_create_membership_success(admin_max_client):
    membership_id = f"m{uuid4().hex[:8]}"
    response = admin_max_client.post(
        "/membership",
        json={
            "id": membership_id,
            "days": 45,
            "price": 149.5,
            "description": "Premium test membership",
        },
    )

    assert response.status_code == 201, (
        f"Failed to create membership: {response.json()}"
    )
    assert response.json().get("message") == "Membership created successfully."


def test_create_membership_failure_existing_id(admin_max_client):
    response = admin_max_client.post(
        "/membership",
        json={
            "id": "weekly",
            "days": 14,
            "price": 100.0,
            "description": "Existing membership",
        },
    )

    assert response.status_code == 400, (
        f"Membership creation should have failed: {response.json()}"
    )
    assert response.json().get("message") == "Membership already exists"


def test_create_membership_not_allowed(admin_min_client):
    response = admin_min_client.post(
        "/membership",
        json={
            "id": f"m{uuid4().hex[:8]}",
            "days": 30,
            "price": 90.0,
            "description": "Forbidden membership",
        },
    )

    assert response.status_code == 403, (
        f"Membership creation should have been forbidden: {response.json()}"
    )
    assert response.json().get("message") == "Forbidden: Unauthorized request"


def test_update_membership_success(admin_max_client, create_membership):
    response = admin_max_client.patch(
        f"/membership/info/{create_membership['id']}",
        json={
            "days": 60,
            "price": 199.99,
            "description": "Updated membership description",
        },
    )

    assert response.status_code == 200, (
        f"Failed to update membership: {response.json()}"
    )
    assert (
        response.json().get("message")
        == f"{create_membership['id']} Membership information updated successfully."
    )


def test_update_membership_not_found(admin_max_client):
    response = admin_max_client.patch(
        f"/membership/info/membership{uuid4().hex}",
        json={"days": 90},
    )

    assert response.status_code == 404
    assert response.json().get("message") == MEMBERSHIP_NOT_FOUND


def test_delete_membership_success(admin_max_client, create_membership):
    response = admin_max_client.delete(f"/membership/info/{create_membership['id']}")

    assert response.status_code == 204, (
        f"Failed to delete membership: {response.json()}"
    )


def test_delete_membership_nonexistent(admin_max_client):
    response = admin_max_client.delete(f"/membership/info/membership{uuid4().hex}")

    assert response.status_code == 404
    assert response.json().get("message") == MEMBERSHIP_NOT_FOUND
