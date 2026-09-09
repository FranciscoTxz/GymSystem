from uuid import uuid4

import pytest

USER_NOT_FOUND = "User not found."
MEMBERSHIP_NOT_FOUND = "Membership not found."


@pytest.fixture(scope="function")
def create_user(admin_min_client):
    email = f"user{uuid4().hex[:8]}@example.com"
    response = admin_min_client.post(
        "/user",
        json={
            "membership": "weekly",
            "first_name": "Ana",
            "last_name": "Garcia",
            "birthdate": "1995-05-15",
            "phone_number": "4491234567",
            "email": email,
            "emergency_contact": "Maria Garcia",
            "photo_url": "https://example.com/avatar.png",
            "fingerprint_template": None,
        },
    )

    assert response.status_code == 201, f"User creation failed: {response.json()}"
    assert response.json().get("message") == "User registered successfully."

    return {"id": response.json().get("user_id"), "email": email}


def test_get_all_users_success(admin_min_client):
    response = admin_min_client.get("/user", params={"next_cursor": None, "limit": 10})

    assert response.status_code == 200, f"Failed to get all users: {response.json()}"
    assert isinstance(response.json().get("items"), list), "Expected a list of users"


def test_get_all_users_success_search_by_name(admin_min_client):
    response = admin_min_client.get(
        "/user", params={"next_cursor": None, "limit": 10, "name": "John"}
    )

    assert response.status_code == 200, f"Failed to search users: {response.json()}"
    assert isinstance(response.json().get("items"), list), "Expected a list of users"
    assert all(
        "John" in user.get("full_name", "") for user in response.json().get("items")
    ), "Expected all users to have 'John' in their full name"


def test_get_user_access_success(admin_min_client):
    response = admin_min_client.get("/user/access/1")

    assert response.status_code == 200, f"Failed to access user: {response.json()}"
    assert response.json().get("message") == "Welcome John Doe! Access granted."
    assert "remaining_days" in response.json()


def test_get_user_info_success(admin_min_client):
    response = admin_min_client.get("/user/info/1")

    assert response.status_code == 200, f"Failed to get user info: {response.json()}"
    assert isinstance(response.json(), dict), "Expected a dictionary with user info"
    assert response.json().get("id") == 1
    assert response.json().get("full_name") == "John Doe"


def test_get_full_user_info_success(admin_min_client):
    response = admin_min_client.get("/user/info/1/full")

    assert response.status_code == 200, (
        f"Failed to get full user info: {response.json()}"
    )
    assert isinstance(response.json(), dict), (
        "Expected a dictionary with full user info"
    )
    assert response.json().get("id") == 1
    assert response.json().get("membership") == "weekly"


def test_get_full_user_info_not_found(admin_min_client):
    response = admin_min_client.get("/user/info/999999/full")

    assert response.status_code == 404
    assert response.json().get("message") == USER_NOT_FOUND


def test_create_user_success(admin_min_client):
    email = f"user{uuid4().hex[:8]}@example.com"
    response = admin_min_client.post(
        "/user",
        json={
            "membership": "weekly",
            "first_name": "Carlos",
            "last_name": "Lopez",
            "birthdate": "1992-02-10",
            "phone_number": "4497654321",
            "email": email,
            "emergency_contact": "Lucia Lopez",
            "photo_url": "https://example.com/carlos.png",
            "fingerprint_template": None,
        },
    )

    assert response.status_code == 201, f"Failed to create user: {response.json()}"
    assert response.json().get("message") == "User registered successfully."
    assert "user_id" in response.json()


def test_create_user_unknown_membership(admin_min_client):
    response = admin_min_client.post(
        "/user",
        json={
            "membership": "unknown_plan",
            "first_name": "Pedro",
            "last_name": "Mendoza",
            "birthdate": "1990-06-20",
            "phone_number": "4491112233",
            "email": f"user{uuid4().hex[:8]}@example.com",
            "emergency_contact": "Laura Mendoza",
            "photo_url": "https://example.com/pedro.png",
            "fingerprint_template": None,
        },
    )

    assert response.status_code == 404
    assert response.json().get("message") == MEMBERSHIP_NOT_FOUND


def test_update_user_info_success(admin_min_client, create_user):
    response = admin_min_client.patch(
        f"/user/info/{create_user['id']}",
        json={
            "phone_number": "4499988776",
            "email": f"updated{uuid4().hex[:6]}@example.com",
            "emergency_contact": "Updated Contact",
            "photo_url": "https://example.com/updated.png",
        },
    )

    assert response.status_code == 200, f"Failed to update user info: {response.json()}"
    assert (
        response.json().get("message")
        == "User Ana Garcia information updated successfully."
    )


def test_update_user_membership_success(admin_min_client, create_user):
    response = admin_min_client.patch(
        f"/user/membership/{create_user['id']}",
        json={"membership": "student"},
    )

    assert response.status_code == 200, (
        f"Failed to update user membership: {response.json()}"
    )
    assert (
        response.json().get("message")
        == "User Ana Garcia membership updated successfully."
    )


def test_update_user_membership_unknown_plan(admin_min_client, create_user):
    response = admin_min_client.patch(
        f"/user/membership/{create_user['id']}",
        json={"membership": "unknown_plan"},
    )

    assert response.status_code == 404
    assert response.json().get("message") == MEMBERSHIP_NOT_FOUND


def test_deactivate_activate_ban_and_delete_user_success(admin_min_client, create_user):
    response = admin_min_client.patch(f"/user/deactivate/{create_user['id']}")
    assert response.status_code == 200, f"Failed to deactivate user: {response.json()}"
    assert (
        response.json().get("message")
        == "User Ana Garcia account deactivated successfully."
    )

    response = admin_min_client.patch(f"/user/activate/{create_user['id']}")
    assert response.status_code == 200, f"Failed to activate user: {response.json()}"
    assert (
        response.json().get("message")
        == "User Ana Garcia account activated successfully."
    )

    response = admin_min_client.patch(f"/user/ban/{create_user['id']}")
    assert response.status_code == 200, f"Failed to ban user: {response.json()}"
    assert response.json().get("message") == "User Ana Garcia has been banned."

    response = admin_min_client.delete(f"/user/delete/{create_user['id']}")
    assert response.status_code == 204, f"Failed to delete user: {response.json()}"


def test_user_mutations_not_found(admin_min_client):
    user_id = 999999

    response = admin_min_client.patch(f"/user/deactivate/{user_id}")
    assert response.status_code == 404
    assert response.json().get("message") == USER_NOT_FOUND

    response = admin_min_client.patch(f"/user/activate/{user_id}")
    assert response.status_code == 404
    assert response.json().get("message") == USER_NOT_FOUND

    response = admin_min_client.patch(f"/user/ban/{user_id}")
    assert response.status_code == 404
    assert response.json().get("message") == USER_NOT_FOUND

    response = admin_min_client.delete(f"/user/delete/{user_id}")
    assert response.status_code == 404
    assert response.json().get("message") == USER_NOT_FOUND
