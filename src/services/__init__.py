import csv
from contextlib import suppress
from hashlib import sha1

from mongoengine import connect, disconnect
from pymongo.errors import PyMongoError

from common.constants import MONGODB_URI
from common.log_helper import get_logger

_LOG = get_logger(__name__)


def connect_to_mongodb() -> None:
    try:
        if MONGODB_URI:
            client = connect(
                host=MONGODB_URI,
                alias="default",
                serverSelectionTimeoutMS=5000,
            )
        else:
            client = connect(
                "gymsystem",
                host="localhost",
                port=27017,
                alias="default",
                serverSelectionTimeoutMS=5000,
            )

        client.admin.command("ping")
        _LOG.info("Connected to MongoDB successfully")
        _seed_admins_table()
        _seed_memberships_table()
    except PyMongoError:
        with suppress(Exception):
            disconnect(alias="default")
        _LOG.error("Error connecting to MongoDB")


def _seed_admins_table() -> None:
    from models.admins import Admins
    from schemas.admin_schema import AdminType

    if Admins.objects.count() == 0:
        _LOG.info("Seeding Admins collection...")
        file_path = "templates/admins_seed_example.csv"
        fieldnames = [
            "email",
            "password",
            "first_name",
            "last_name",
            "birthdate",
            "phone_number",
        ]
        with open(file_path, encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # skip header
            for row in reader:
                row_dict = dict(zip(fieldnames, row))
                Admins(
                    email=row_dict["email"],
                    password_hash=sha1(
                        f"{row_dict['password']}{row_dict['email']}".encode()
                    ).hexdigest(),
                    first_name=row_dict["first_name"],
                    last_name=row_dict["last_name"],
                    full_name=f"{row_dict['first_name']} {row_dict['last_name']}",
                    birthdate=row_dict["birthdate"],
                    phone_number=row_dict["phone_number"],
                    type=AdminType.MAX,
                ).save()

        _LOG.info("Admins collection seeded successfully")


def _seed_memberships_table() -> None:
    from models.memberships import Memberships

    if Memberships.objects.count() == 0:
        _LOG.info("Seeding Memberships collection...")
        file_path = "templates/memberships_seed_example.csv"
        fieldnames = ["id", "days", "price", "description"]

        with open(file_path, encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # skip header
            for row in reader:
                row_dict = dict(zip(fieldnames, row))
                Memberships(
                    id=row_dict["id"],
                    days=int(row_dict["days"]),
                    price=float(row_dict["price"]),
                    description=row_dict["description"],
                ).save()

        _LOG.info("Memberships collection seeded successfully")


def disconnect_from_mongodb() -> None:
    disconnect(alias="default")
    _LOG.info("Disconnected from MongoDB successfully")
