import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from services import send_notifications_report_service as notification_module


async def _stop_sleep(seconds):
    raise asyncio.CancelledError


def test_soon_expired_notifications_sends_only_to_users_with_email(monkeypatch):
    users = [
        SimpleNamespace(full_name="Ada", email="ada@example.com"),
        SimpleNamespace(full_name="No Email", email=None),
    ]
    objects = MagicMock()
    objects.return_value.only.return_value = users
    monkeypatch.setattr(notification_module, "Users", SimpleNamespace(objects=objects))
    send_email = MagicMock()

    async def send(**kwargs):
        send_email(**kwargs)

    monkeypatch.setattr(
        notification_module.EmailService, "send_email_notification", send
    )
    monkeypatch.setattr(notification_module.asyncio, "sleep", _stop_sleep)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(notification_module.send_soon_expired_notifications())

    send_email.assert_called_once()


@pytest.mark.parametrize("weekday,expected_calls", [(4, 1), (0, 0)])
def test_statistics_notification_runs_only_on_friday(
    monkeypatch, weekday, expected_calls
):
    now = SimpleNamespace(year=2026, month=9, weekday=lambda: weekday)
    monkeypatch.setattr(
        notification_module, "datetime", SimpleNamespace(now=lambda tz: now)
    )
    statistics = [
        SimpleNamespace(
            to_mongo=lambda: SimpleNamespace(to_dict=lambda: {"membership": "basic"})
        )
    ]
    objects = MagicMock()
    objects.return_value.only.return_value = statistics
    monkeypatch.setattr(
        notification_module, "Statistics", SimpleNamespace(objects=objects)
    )
    sent = MagicMock()

    async def send(**kwargs):
        sent(**kwargs)

    monkeypatch.setattr(
        notification_module.EmailService, "send_statistics_report", send
    )
    monkeypatch.setattr(notification_module.asyncio, "sleep", _stop_sleep)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(notification_module.send_statistics_report())

    assert sent.call_count == expected_calls
