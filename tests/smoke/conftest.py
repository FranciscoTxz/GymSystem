import csv
import os
import time
from collections.abc import Generator
from datetime import datetime, timedelta
from hashlib import sha1
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from mongoengine.connection import get_db
from pymongo import MongoClient
from testcontainers.core.container import DockerContainer

from models.admins import Admins
from models.memberships import Memberships
from models.statistics import Statistics
from models.users import Users
from schemas.admin_schema import AdminType
from services.email_service import EmailService

TABLES = [Statistics]
FIXED_TABLES = [Admins, Memberships, Users]


# Mock admin MAX constants
ADMIN_EMAIL = "fake@admin.com"
ADMIN_PASSWORD = "AdminPass123!"
ADMIN_NAME = "Frank"
ADMIN_SURNAME = "Thompson"
ADMIN_BIRTHDATE = "1997-01-01"
ADMIN_PHONE = "1231231234"
ADMIN_TYPE = AdminType.MAX


# Mock admin MIN constants
ADMIN2_EMAIL = "fake_min@admin.com"
ADMIN2_PASSWORD = "AdminPass123!"
ADMIN2_NAME = "John"
ADMIN2_SURNAME = "Thomson"
ADMIN2_BIRTHDATE = "1997-04-04"
ADMIN2_PHONE = "1231231234"
ADMIN2_TYPE = AdminType.MIN

ADMINS_FIXTURE_DATA = [
    {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "first_name": ADMIN_NAME,
        "last_name": ADMIN_SURNAME,
        "full_name": f"{ADMIN_NAME} {ADMIN_SURNAME}",
        "birthdate": ADMIN_BIRTHDATE,
        "phone_number": ADMIN_PHONE,
        "type": ADMIN_TYPE,
    },
    {
        "email": ADMIN2_EMAIL,
        "password": ADMIN2_PASSWORD,
        "first_name": ADMIN2_NAME,
        "last_name": ADMIN2_SURNAME,
        "full_name": f"{ADMIN2_NAME} {ADMIN2_SURNAME}",
        "birthdate": ADMIN2_BIRTHDATE,
        "phone_number": ADMIN2_PHONE,
        "type": ADMIN2_TYPE,
    },
]

USERS_FIXTURE_DATA = [
    {
        "id": 1,
        "membership": "weekly",
        "first_name": "John",
        "last_name": "Doe",
        "birthdate": "1990-01-01",
        "phone_number": "1234567890",
        "email": "john.doe@example.com",
        "emergency_contact": "Jane Doe",
        "next_payment": datetime.now(tz=ZoneInfo("America/Mexico_City")).date()
        + timedelta(days=7),
    }
]


@pytest.fixture(scope="session")
def user_info():
    return USERS_FIXTURE_DATA[0]


@pytest.fixture(scope="session")
def admin_info_max():
    return ADMINS_FIXTURE_DATA[0]


@pytest.fixture(scope="session")
def admin_info_min():
    return ADMINS_FIXTURE_DATA[1]


def wait_until_ready(mongo_uri: str, timeout: float = 15):
    deadline = time.time() + timeout
    while True:
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
            client.admin.command("ping")
            return
        except Exception:
            if time.time() > deadline:
                raise
            time.sleep(0.5)


@pytest.fixture(scope="session")
def mongodb_container() -> Generator[str, None, None]:
    """
    Starts MongoDB in Docker for the test session and returns a connection URI.
    """
    with DockerContainer("mongo:7.0").with_exposed_ports(27017) as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(27017)
        mongo_uri = f"mongodb://{host}:{port}/clinic_db"
        wait_until_ready(mongo_uri)
        yield mongo_uri


@pytest.fixture(scope="session")
def mongo_connection(mongodb_container):
    os.environ["MONGODB_URI"] = mongodb_container
    from common import constants

    constants.MONGODB_URI = mongodb_container
    connect(host=mongodb_container, alias="default")
    yield
    disconnect(alias="default")


@pytest.fixture(scope="session")
def create_fixed_tables(mongo_connection):
    for model in FIXED_TABLES + TABLES:
        model.drop_collection()

    file_path = os.path.join(
        os.path.dirname(__file__), "templates", "memberships_seed_test.csv"
    )
    with open(file_path, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            Memberships(
                id=row["id"],
                days=int(row["days"]),
                price=row["price"],
                description=row["description"],
            ).save()

    for admin in ADMINS_FIXTURE_DATA:
        password_hash = sha1(
            f"{admin['password']}{admin['email']}".encode()
        ).hexdigest()
        Admins(
            email=admin["email"],
            password_hash=password_hash,
            first_name=admin["first_name"],
            last_name=admin["last_name"],
            full_name=f"{admin['first_name']} {admin['last_name']}",
            birthdate=admin["birthdate"],
            phone_number=admin["phone_number"],
            type=admin["type"],
        ).save()

    for user in USERS_FIXTURE_DATA:
        Users(
            id=user["id"],
            membership=user["membership"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            full_name=f"{user['first_name']} {user['last_name']}",
            birthdate=user["birthdate"],
            phone_number=user["phone_number"],
            email=user["email"],
            emergency_contact=user["emergency_contact"],
            next_payment=user["next_payment"],
        ).save()

    yield

    for model in FIXED_TABLES + TABLES:
        model.drop_collection()


@pytest.fixture(scope="function")
def dynamic_client(create_fixed_tables):
    for model in TABLES:
        model.drop_collection()

    yield get_db()

    for model in TABLES:
        model.drop_collection()


@pytest.fixture(scope="function", autouse=True)
def patch_external_clients(monkeypatch):
    monkeypatch.setattr(
        EmailService,
        "send_email_notification",
        lambda **kwargs: {},
    )
    monkeypatch.setattr(
        EmailService,
        "send_statistics_report",
        lambda **kwargs: {},
    )


@pytest.fixture(scope="function")
def admin_max_client(create_fixed_tables) -> TestClient:
    return _login_client(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="function")
def admin_min_client(create_fixed_tables) -> TestClient:
    return _login_client(ADMIN2_EMAIL, ADMIN2_PASSWORD)


def _login_client(email: str, password: str) -> TestClient:
    from app import app

    client = TestClient(app)

    login_response = client.post(
        "/admin/sign-in",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
    token = login_response.json().get("access_token")

    client.headers.update({"authorization": token})

    return client
