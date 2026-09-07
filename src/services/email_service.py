import smtplib
import ssl

# from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import certifi

from common.constants import SENDER_EMAIL, SENDER_PASSWORD
from common.log_helper import get_logger

_LOG = get_logger(__name__)


class EmailService:
    @staticmethod
    def _get_report_template(
        full_name: str,
        reason: str,
    ) -> str:
        """
        Generate HTML template for the review email.
        Loads template from file and replaces placeholders.
        """
        template_path = (
            Path(__file__).parent.parent / "templates" / "notification_template.html"
        )
        with open(template_path, encoding="utf-8") as f:
            template = f.read()

        return template.format(full_name=full_name, reason=reason)

    @staticmethod
    async def send_email_notification(
        to_email: str,
        full_name: str,
        body: str,
        subject: str = "Membership Expiration Notice",
        smtp_server: str = "smtp.gmail.com",
        port: int = 465,
    ):
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            _LOG.warning(
                "Email credentials not set in environment variables. Skipping email sending."
            )
            return

        target_email = to_email

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = target_email

        html_content = EmailService._get_report_template(full_name, body)
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            context = ssl.create_default_context(cafile=certifi.where())
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            _LOG.info("Email sent successfully to %s", target_email)
        except (smtplib.SMTPException, ssl.SSLError, OSError) as e:
            _LOG.exception("Failed to send email: %s", e)
