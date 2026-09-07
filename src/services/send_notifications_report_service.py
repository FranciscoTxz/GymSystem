import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from common.constants import ADMIN_EMAIL
from common.log_helper import get_logger
from models.statistics import Statistics
from models.users import Users
from schemas.user_schema import UserState
from services.email_service import EmailService

_LOG = get_logger(__name__)


async def send_soon_expired_notifications():
    while True:
        _LOG.info("Checking memberships to expire soon...")
        next_payment = datetime.now(tz=ZoneInfo("America/Mexico_City")) + timedelta(
            days=7
        )
        users_emails = Users.objects(
            next_payment=next_payment, state=UserState.active
        ).only("full_name", "email", "next_payment")

        for user in users_emails:
            _LOG.info(
                "Sending notification to user: %s <%s>", user.full_name, user.email
            )
            if user.email is not None:
                await EmailService.send_email_notification(
                    to_email=user.email,
                    full_name=user.full_name,
                    subject="Membership Expiration Notice",
                    body="Your membership will expire soon.  Please make the necessary arrangements to renew it.",
                )
        await asyncio.sleep(86450)


async def send_statistics_report():
    while True:
        now = datetime.now(tz=ZoneInfo("America/Mexico_City"))

        # if now.weekday() == 4:
        if now.weekday() == 0:
            _LOG.info("Generating monthly statistics report ...")
            statistics = Statistics.objects(year=now.year, month=now.month).only(
                "membership", "sold_memberships", "amount"
            )

            statistics_dict = [
                statistic.to_mongo().to_dict() for statistic in statistics
            ]
            await EmailService.send_statistics_report(
                to_email=ADMIN_EMAIL or "", statistics=statistics_dict
            )

        await asyncio.sleep(86450)
