"""Email delivery adapters for identity verification.

The development backend intentionally writes the one-time token to application logs.
It must never be enabled in production. SMTP is the production-capable adapter;
credentials are read only from environment variables and never logged.
"""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class EmailDeliveryFailure(RuntimeError):
    """Raised when a verification message cannot be delivered."""


def send_verification_email(*, recipient: str, token: str) -> None:
    backend = os.getenv("EMAIL_BACKEND", "log").strip().lower()
    app_environment = os.getenv("APP_ENV", "production").strip().lower()

    if backend == "log":
        if app_environment not in {"development", "test"}:
            raise EmailDeliveryFailure(
                "The log email backend is forbidden outside development/test."
            )
        logger.warning(
            "DEVELOPMENT-ONLY EMAIL VERIFICATION: recipient=%s token=%s",
            recipient,
            token,
        )
        return

    if backend != "smtp":
        raise EmailDeliveryFailure("EMAIL_BACKEND must be 'log' or 'smtp'.")

    host = os.getenv("SMTP_HOST", "").strip()
    sender = os.getenv("EMAIL_FROM", "").strip()
    if not host or not sender:
        raise EmailDeliveryFailure("SMTP_HOST and EMAIL_FROM are required for SMTP delivery.")

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME", "")
        password = os.getenv("SMTP_PASSWORD", "")
        starttls = os.getenv("SMTP_STARTTLS", "true").strip().lower() in {"1", "true", "yes"}
        message = EmailMessage()
        message["Subject"] = "Verify your MyEconomy account"
        message["From"] = sender
        message["To"] = recipient
        api_base = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000").rstrip("/")
        message.set_content(
            "A verification request was made for your MyEconomy account.\n\n"
            f"Submit this one-time token to POST {api_base}/api/v1/auth/verify-email "
            'with JSON body {"token": "YOUR_TOKEN"}:\n\n'
            f"{token}\n\n"
            "This token expires in 24 hours. If you did not request this, ignore this message."
        )
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if starttls:
                smtp.starttls(context=context)
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
    except (OSError, ValueError, smtplib.SMTPException) as exc:
        raise EmailDeliveryFailure("Verification email delivery failed.") from exc
