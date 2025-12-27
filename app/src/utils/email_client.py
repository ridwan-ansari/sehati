from __future__ import annotations
import smtplib
from email.message import EmailMessage
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from app.src.core.config import settings


class EmailClient:
    def __init__(self):
        self.is_ssl = settings.SMTP_IS_SSL
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

    def _send(self, recipient: str, subject: str, html_body: str, text_body: str, use_ssl: bool = True):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = recipient
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        try:
            if self.is_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
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

    def send_password_reset_email(
            self, 
            recipient: str, 
            fullname: str, 
            link: str = "", 
            code: int = None, 
            template_name: str = "emails/reset_password_admin.html"
        ):
        context = {"fullname": fullname, "link": link, "code":code, "year": datetime.utcnow().year}
        html = self._render(template_name, context)
        self._send(recipient, "SEHATI — Password Reset Request", html, "")

    def send_claim_marchandise_notification(self, recipient: str, context: dict):
        html = self._render(template_name="emails/claim_marchandise.html", context=context)
        self._send(recipient, "SEHATI — Merchandise Claim Request", html, "")
    
    def send_approve_claim_marchandise(self, recipient: str, context: dict):
        html = self._render(template_name="emails/approve_claim_merchandise.html", context=context)
        self._send(recipient, "SEHATI — Merchandise Claim Approved", html, "")
    
    def send_rejected_claim_marchandise(self, recipient: str, context: dict):
        html = self._render(template_name="emails/rejected_claim.html", context=context)
        self._send(recipient, "SEHATI — Merchandise Claim Rejected", html, "")
    
    def send_appointment(self, recipient: str, context: dict):
        html = self._render(template_name="emails/appointment_notification.html", context=context)
        self._send(recipient, "SEHATI — New Appointment Request", html, "")

email_client = EmailClient()
