from __future__ import annotations
import smtplib
from email.message import EmailMessage
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from app.src.core.config import settings


class EmailClient:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_pass = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_SENDER

        # Tentukan folder template utama (misalnya app/src/templates)
        templates_dir = Path("app/src/templates")
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _render(self, template_path: str, context: dict) -> str:
        tpl = self.env.get_template(template_path)
        return tpl.render(**context)

    def send_verification_email(self, recipient: str, code: int, fullname: str | None = None):
        """Kirim email HTML verifikasi dengan kode OTP 6 digit."""
        context = {
            "fullname": fullname,
            "code": f"{code:06d}",
            "year": datetime.utcnow().year,
        }

        html_body = self._render("emails/verify.html", context)
        text_body = (
            f"Hi {fullname or 'there'},\n\n"
            f"Your verification code is: {code:06d}\n"
            "This code expires in 10 minutes.\n\n"
            "— MRA Security Team"
        )

        msg = EmailMessage()
        msg["Subject"] = "MRA — Verify your account"
        msg["From"] = self.from_email
        msg["To"] = recipient
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
        except Exception as e:
            raise RuntimeError(f"Failed to send verification email: {e}")
