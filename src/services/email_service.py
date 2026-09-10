import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from pathlib import Path

import certifi
import matplotlib

from common.constants import SENDER_EMAIL, SENDER_PASSWORD
from common.log_helper import get_logger

matplotlib.use("Agg")
import matplotlib.pyplot as plt

_LOG = get_logger(__name__)


class EmailService:
    @staticmethod
    def _get_notification_template(
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
    def _get_statistics_template(statistics: list[dict]) -> str:
        """
        Generate HTML template for the statistics report email.
        Loads template from file, embeds the totals summary and grand total as text.
        """
        template_path = (
            Path(__file__).parent.parent / "templates" / "statistics_template.html"
        )
        with open(template_path, encoding="utf-8") as f:
            template = f.read()

        summary_rows = "".join(
            f'<tr><td style="padding: 4px 0; color: #4a5568; font-size: 14px;">{s["membership"]}</td>'
            f'<td style="padding: 4px 0; color: #2d3748; font-size: 14px; font-weight: 600; text-align: right;">'
            f"${s['amount']:.2f}</td></tr>"
            for s in statistics
        )
        grand_total = sum(s["amount"] for s in statistics)

        return template.format(
            summary_rows=summary_rows, grand_total=f"{grand_total:.2f}"
        )

    @staticmethod
    def _generate_bar_chart(statistics: list[dict]) -> bytes:
        """Bar chart of sold memberships count per membership type."""
        memberships = [s["membership"] for s in statistics]
        counts = [s["sold_memberships"] for s in statistics]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(memberships, counts, color="#667eea")
        ax.set_xlabel("Membership")
        ax.set_ylabel("Sold Memberships")
        ax.set_title("Sold Memberships by Membership Type")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        fig.tight_layout()

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        plt.close(fig)
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def _generate_pie_chart(statistics: list[dict]) -> bytes:
        """Pie chart of total amount sold per membership type."""
        memberships = [s["membership"] for s in statistics]
        amounts = [s["amount"] for s in statistics]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(amounts, labels=memberships, autopct="%1.1f%%")
        ax.set_title("Total Amount Sold by Membership Type")
        fig.tight_layout()

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        plt.close(fig)
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def _attach_inline_image(
        msg: MIMEMultipart, image_bytes: bytes, content_id: str
    ) -> None:
        image = MIMEImage(image_bytes, _subtype="png")
        image.add_header("Content-ID", f"<{content_id}>")
        image.add_header("Content-Disposition", "inline", filename=f"{content_id}.png")
        msg.attach(image)

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

        html_content = EmailService._get_notification_template(full_name, body)
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            context = ssl.create_default_context(cafile=certifi.where())
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            _LOG.info("Email sent successfully to %s", target_email)
        except (smtplib.SMTPException, ssl.SSLError, OSError) as e:
            _LOG.exception("Failed to send email: %s", e)

    @staticmethod
    async def send_statistics_report(
        to_email: str,
        statistics,
        subject: str = "Monthly Statistics Report",
        smtp_server: str = "smtp.gmail.com",
        port: int = 465,
    ):
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            _LOG.warning(
                "Email credentials not set in environment variables. Skipping email sending."
            )
            return

        target_email = to_email

        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = target_email

        html_content = EmailService._get_statistics_template(statistics or [])
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        if statistics:
            bar_chart = EmailService._generate_bar_chart(statistics)
            pie_chart = EmailService._generate_pie_chart(statistics)
            EmailService._attach_inline_image(msg, bar_chart, "bar_chart")
            EmailService._attach_inline_image(msg, pie_chart, "pie_chart")

        try:
            context = ssl.create_default_context(cafile=certifi.where())
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            _LOG.info("Email sent successfully to %s", target_email)
        except (smtplib.SMTPException, ssl.SSLError, OSError) as e:
            _LOG.exception("Failed to send email: %s", e)
