import asyncio
import smtplib
from unittest.mock import MagicMock, mock_open

from services import email_service as email_module
from services.email_service import EmailService


def _smtp(monkeypatch):
    server = MagicMock()
    smtp = MagicMock()
    smtp.return_value.__enter__.return_value = server
    monkeypatch.setattr(email_module.smtplib, "SMTP_SSL", smtp)
    monkeypatch.setattr(email_module.ssl, "create_default_context", MagicMock())
    return server


def test_templates_and_charts_render_content(monkeypatch):
    monkeypatch.setattr("builtins.open", mock_open(read_data="{full_name} {reason}"))
    statistics = [{"membership": "basic", "sold_memberships": 2, "amount": 300.0}]

    assert EmailService._get_notification_template("Ada", "Expires") == "Ada Expires"
    monkeypatch.setattr(
        "builtins.open", mock_open(read_data="{summary_rows} {grand_total}")
    )
    assert "300.00" in EmailService._get_statistics_template(statistics)
    assert EmailService._generate_bar_chart(statistics).startswith(b"\x89PNG")
    assert EmailService._generate_pie_chart(statistics).startswith(b"\x89PNG")


def test_attach_inline_image_adds_image_part():
    message = email_module.MIMEMultipart()
    EmailService._attach_inline_image(message, b"image", "chart")
    part = message.get_payload()[0]
    assert part["Content-ID"] == "<chart>"
    assert part["Content-Disposition"] == 'inline; filename="chart.png"'


def test_notification_skips_when_credentials_missing(monkeypatch):
    logger = MagicMock()
    monkeypatch.setattr(email_module, "SENDER_EMAIL", None)
    monkeypatch.setattr(email_module, "SENDER_PASSWORD", None)
    monkeypatch.setattr(email_module, "_LOG", logger)

    asyncio.run(EmailService.send_email_notification("a@example.com", "Ada", "Body"))

    logger.warning.assert_called_once()


def test_notification_sends_and_logs_smtp_error(monkeypatch):
    monkeypatch.setattr(email_module, "SENDER_EMAIL", "sender@example.com")
    monkeypatch.setattr(email_module, "SENDER_PASSWORD", "password")
    monkeypatch.setattr(
        EmailService, "_get_notification_template", lambda *args: "<p>body</p>"
    )
    logger = MagicMock()
    monkeypatch.setattr(email_module, "_LOG", logger)
    server = _smtp(monkeypatch)

    asyncio.run(EmailService.send_email_notification("a@example.com", "Ada", "Body"))
    server.login.assert_called_once_with("sender@example.com", "password")
    server.send_message.assert_called_once()
    logger.info.assert_called_once()

    server.send_message.side_effect = smtplib.SMTPException("failed")
    asyncio.run(EmailService.send_email_notification("a@example.com", "Ada", "Body"))
    logger.exception.assert_called_once()


def test_statistics_report_skips_or_sends_with_optional_charts(monkeypatch):
    logger = MagicMock()
    monkeypatch.setattr(email_module, "_LOG", logger)
    monkeypatch.setattr(email_module, "SENDER_EMAIL", None)
    monkeypatch.setattr(email_module, "SENDER_PASSWORD", None)
    asyncio.run(EmailService.send_statistics_report("admin@example.com", []))
    logger.warning.assert_called_once()

    monkeypatch.setattr(email_module, "SENDER_EMAIL", "sender@example.com")
    monkeypatch.setattr(email_module, "SENDER_PASSWORD", "password")
    monkeypatch.setattr(
        EmailService, "_get_statistics_template", lambda statistics: "<p>report</p>"
    )
    bar_chart = MagicMock(return_value=b"bar")
    pie_chart = MagicMock(return_value=b"pie")
    attach = MagicMock()
    monkeypatch.setattr(EmailService, "_generate_bar_chart", bar_chart)
    monkeypatch.setattr(EmailService, "_generate_pie_chart", pie_chart)
    monkeypatch.setattr(EmailService, "_attach_inline_image", attach)
    server = _smtp(monkeypatch)

    asyncio.run(EmailService.send_statistics_report("admin@example.com", []))
    asyncio.run(
        EmailService.send_statistics_report(
            "admin@example.com", [{"membership": "basic"}]
        )
    )

    assert server.send_message.call_count == 2
    bar_chart.assert_called_once()
    pie_chart.assert_called_once()
    assert attach.call_count == 2
    server.send_message.side_effect = smtplib.SMTPException("failed")
    asyncio.run(EmailService.send_statistics_report("admin@example.com", []))
    logger.exception.assert_called_once()
