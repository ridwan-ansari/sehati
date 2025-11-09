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

        self.env = Environment(
            loader=FileSystemLoader(str(Path("app/src/templates"))),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _render(self, template_name: str, context: dict) -> str:
        return self.env.get_template(template_name).render(**context)

    def _send(self, recipient: str, subject: str, html_body: str, text_body: str):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = recipient
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        try:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
        except Exception as e:
            raise RuntimeError(f"Failed to send email: {e}")

    def send_verification_email(self, recipient: str, code: int, fullname: str | None = None):
        context = {
            "fullname": fullname,
            "code": f"{code:06d}",
            "year": datetime.utcnow().year,
        }
        html = self._render("emails/verify.html", context)
        text = (
            f"Hi {fullname or 'there'},\n\n"
            f"Your verification code is: {code:06d}\n"
            "This code expires in 10 minutes.\n\n"
            "— SEHATI Security Team"
        )
        self._send(recipient, "SEHATI — Verify Your Account", html, text)

    def send_password_reset_email(self, recipient: str, fullname: str, link: str):
        context = {"fullname": fullname, "link": link, "year": datetime.utcnow().year}
        html = self._render("emails/reset_password_admin.html", context)
        text = (
            f"Hi {fullname},\n\n"
            f"Click the link below to reset your password:\n{link}\n\n"
            "If you didn’t request this, please ignore it.\n\n"
            "— SEHATI Security Team"
        )
        self._send(recipient, "SEHATI — Password Reset Request", html, text)
