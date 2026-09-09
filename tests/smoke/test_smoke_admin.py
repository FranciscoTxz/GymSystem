import random
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from schemas.admin_schema import AdminInfo, AdminInfoFull

ADMIN_NOT_FOUND = "Admin profile not found."


def random_name():
    first_name = random.choice(
        [
            "Francisco",
            "Luis",
            "Andrea",
            "Sofía",
            "Carlos",
            "Ana",
            "Miguel",
            "Isabella",
            "Valentina",
            "Gabriel",
            "Camila",
        ]
    )
    last_name = random.choice(
        [
            "Torres",
            "González",
            "López",
            "Martínez",
            "Hernández",
            "Ramírez",
            "Cruz",
            "Flores",
            "Sánchez",
            "Rojas",
        ]
    )
    return first_name, last_name


@pytest.fixture(scope="function")
def create_simple_admin(admin_max_client):
    email = f"admin{uuid4()}@example.com"
    name, last_name = random_name()
    test_password = "PassWord1234@"
    signup_resonse = admin_max_client.post(
        "/admin/sign-up",
        json={
            "email": email,
            "password": test_password,
            "first_name": name,
            "last_name": last_name,
            "birthdate": "2002-07-19",
            "phone_number": "4492003399",
            "type": "MAX",
        },
    )

    assert signup_resonse.status_code == 201, f"Sign-up failed: {signup_resonse.json()}"
    assert signup_resonse.json().get("message") == "Admin registered successfully."

    return {
        "email": email,
        "password": test_password,
        "first_name": name,
        "last_name": last_name,
        "full_name": f"{name} {last_name}",
    }


def test_sign_in_success(dynamic_client, admin_info_max):
    from app import app

    client = TestClient(app)

    login_response = client.post(
        "/admin/sign-in",
        json={
            "email": admin_info_max["email"],
            "password": admin_info_max["password"],
        },
    )

    assert login_response.status_code == 200, f"Sign-in failed: {login_response.json()}"
    assert "access_token" in login_response.json(), (
        "No access token returned on successful sign-in"
    )


def test_sign_in_failure_wrong_password(dynamic_client, admin_info_max):
    from app import app

    client = TestClient(app)

    login_response = client.post(
        "/admin/sign-in",
        json={
            "email": admin_info_max["email"],
            "password": "WrongPass1234@",
        },
    )

    assert login_response.status_code == 401, (
        f"Sign-in should have failed: {login_response.json()}"
    )
    assert login_response.json().get("message") == "Invalid email or password", (
        "Unexpected error message on failed sign-in"
    )


def test_sign_up_success(admin_max_client):
    signup_resonse = admin_max_client.post(
        "/admin/sign-up",
        json={
            "email": f"admin{uuid4()}@example.com",
            "password": "PassWord1234@",
            "first_name": "Francisco",
            "last_name": "Torres",
            "birthdate": "2002-07-19",
            "phone_number": "4492003399",
            "type": "MAX",
        },
    )

    assert signup_resonse.status_code == 201, f"Sign-up failed: {signup_resonse.json()}"
    assert signup_resonse.json().get("message") == "Admin registered successfully."


def test_sign_up_failure_existing_email(admin_max_client, admin_info_max):
    signup_resonse = admin_max_client.post(
        "/admin/sign-up",
        json={
            "email": admin_info_max["email"],
            "password": "PassWord1234@",
            "first_name": "Francisco",
            "last_name": "Torres",
            "birthdate": "2002-07-19",
            "phone_number": "4492003399",
            "type": "MAX",
        },
    )

    assert signup_resonse.status_code == 400, (
        f"Sign-up should have failed: {signup_resonse.json()}"
    )
    assert (
        signup_resonse.json().get("message") == "Invalid input or email already exists"
    )


def test_sign_up_admin_not_allowed(admin_min_client):
    signup_resonse = admin_min_client.post(
        "/admin/sign-up",
        json={
            "email": f"admin{uuid4()}@example.com",
            "password": "PassWord1234@",
            "first_name": "Francisco",
            "last_name": "Torres",
            "birthdate": "2002-07-19",
            "phone_number": "4492003399",
            "type": "MAX",
        },
    )

    assert signup_resonse.status_code == 403, (
        f"Sign-up should have been forbidden: {signup_resonse.json()}"
    )
    assert signup_resonse.json().get("message") == "Forbidden: Unauthorized request"


def test_get_all_admins_success(admin_max_client):
    response = admin_max_client.get("/admin", params={"next_cursor": None, "limit": 10})
    assert response.status_code == 200, f"Failed to get all admins: {response.json()}"
    assert isinstance(response.json().get("items"), list), "Expected a list of admins"


def test_get_all_admins_success_search_by_name(admin_max_client):
    response = admin_max_client.get(
        "/admin", params={"next_cursor": None, "limit": 10, "name": "Fran"}
    )
    assert response.status_code == 200, f"Failed to get all admins: {response.json()}"
    assert isinstance(response.json().get("items"), list), "Expected a list of admins"
    print(response.json().get("items"))
    assert all(
        "Fran" in admin.get("full_name", "") for admin in response.json().get("items")
    ), "Expected all admins to have 'Fran' in their first name"


def test_get_admin_info_success(admin_min_client):
    response = admin_min_client.get("/admin/info")
    assert response.status_code == 200, f"Failed to get admin info: {response.json()}"
    assert isinstance(response.json(), dict), "Expected a dictionary with admin info"
    assert set(response.json().keys()) == set(
        AdminInfo.model_json_schema()["properties"].keys()
    ), "Admin info keys mismatch"


def test_get_full_admin_info_success(admin_max_client, admin_info_min):
    response = admin_max_client.get(f"/admin/info/{admin_info_min['email']}")
    assert response.status_code == 200, f"Failed to get admin info: {response.json()}"
    assert isinstance(response.json(), dict), "Expected a dictionary with admin info"
    assert set(response.json().keys()) == set(
        AdminInfoFull.model_json_schema()["properties"].keys()
    ), "Admin info keys mismatch"


def test_get_full_admin_info_not_found(admin_max_client):
    response = admin_max_client.get(f"/admin/info/admin{uuid4()}@example.com")
    assert response.status_code == 404
    assert response.json().get("message") == ADMIN_NOT_FOUND


def test_update_admin_info_success(admin_max_client, create_simple_admin):

    response = admin_max_client.patch(
        "/admin/info",
        json={
            "email": create_simple_admin["email"],
            "phone_number": "1234567890",
            "type": "MAX",
        },
    )
    assert response.status_code == 200, (
        f"Failed to update admin info: {response.json()}"
    )
    assert (
        response.json().get("message")
        == f"Admin {create_simple_admin['full_name']} information updated successfully."
    )


def test_update_admin_info_admin_not_found(admin_max_client):

    response = admin_max_client.patch(
        "/admin/info",
        json={
            "email": f"admin{uuid4()}@example.com",
            "phone_number": "1234567890",
            "type": "MAX",
        },
    )
    assert response.status_code == 404, (
        f"Failed to update admin info: {response.json()}"
    )
    assert response.json().get("message") == ADMIN_NOT_FOUND


def test_update_admin_password_success(admin_min_client, admin_info_min):
    test_password = "TestWord1234@"
    response = admin_min_client.patch(
        "/admin/password",
        json={
            "old_password": admin_info_min["password"],
            "new_password": test_password,
        },
    )
    assert response.status_code == 200, (
        f"Failed to update admin password: {response.json()}"
    )
    assert (
        response.json().get("message")
        == f"Admin {admin_info_min['first_name']} {admin_info_min['last_name']} password updated successfully."
    )

    response = admin_min_client.patch(
        "/admin/password",
        json={
            "old_password": test_password,
            "new_password": admin_info_min["password"],
        },
    )
    assert response.status_code == 200, (
        f"Failed to update admin password: {response.json()}"
    )
    assert (
        response.json().get("message")
        == f"Admin {admin_info_min['first_name']} {admin_info_min['last_name']} password updated successfully."
    )


def test_update_admin_password_incorrect_old_password(admin_min_client, admin_info_min):
    test_password = "TestWord1234@"
    response = admin_min_client.patch(
        "/admin/password",
        json={
            "old_password": test_password,
            "new_password": test_password,
        },
    )
    assert response.status_code == 400
    assert response.json().get("message") == "Invalid old password"


def test_deactivate_reactivate_and_delete_admin_success(
    admin_max_client, create_simple_admin
):
    response = admin_max_client.delete(
        f"/admin/deactivate/{create_simple_admin['email']}"
    )
    assert response.status_code == 204, f"Failed to deactivate admin: {response.json()}"

    response = admin_max_client.patch(f"/admin/activate/{create_simple_admin['email']}")
    assert response.status_code == 200, f"Failed to reactivate admin: {response.json()}"
    assert (
        response.json().get("message")
        == f"Admin {create_simple_admin['full_name']} account activated successfully."
    )

    response = admin_max_client.delete(f"/admin/delete/{create_simple_admin['email']}")
    assert response.status_code == 204, f"Failed to delete admin: {response.json()}"


def test_deactivate_nonexistent_admin(admin_max_client):
    response = admin_max_client.delete("/admin/deactivate/nonexistent@example.com")
    assert response.status_code == 404, (
        f"Failed to handle deactivation of nonexistent admin: {response.json()}"
    )
    assert response.json().get("message") == ADMIN_NOT_FOUND


def test_activate_nonexistent_admin(admin_max_client):
    response = admin_max_client.patch("/admin/activate/nonexistent@example.com")
    assert response.status_code == 404, (
        f"Failed to handle activation of nonexistent admin: {response.json()}"
    )
    assert response.json().get("message") == ADMIN_NOT_FOUND


def test_delete_nonexistent_admin(admin_max_client):
    response = admin_max_client.delete("/admin/delete/nonexistent@example.com")
    assert response.status_code == 404, (
        f"Failed to handle deletion of nonexistent admin: {response.json()}"
    )
    assert response.json().get("message") == ADMIN_NOT_FOUND
