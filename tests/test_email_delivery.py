from __future__ import annotations

import logging
from email.message import EmailMessage

import pytest

from myeconomy.infrastructure import email_delivery
from myeconomy.infrastructure.email_delivery import (
    EmailDeliveryFailure,
    send_verification_email,
)


def test_development_log_adapter_is_explicit_and_contains_challenge(caplog, monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("EMAIL_BACKEND", "log")

    with caplog.at_level(logging.WARNING):
        send_verification_email(recipient="person@example.com", token="synthetic-token")

    assert "person@example.com" in caplog.text
    assert "synthetic-token" in caplog.text


def test_log_adapter_is_rejected_outside_development_and_test(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("EMAIL_BACKEND", "log")

    with pytest.raises(EmailDeliveryFailure, match="forbidden"):
        send_verification_email(recipient="person@example.com", token="synthetic-token")


def test_smtp_backend_requires_host_and_sender(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("EMAIL_FROM", raising=False)

    with pytest.raises(EmailDeliveryFailure, match="SMTP_HOST and EMAIL_FROM"):
        send_verification_email(recipient="person@example.com", token="synthetic-token")


def test_smtp_backend_sends_message_over_starttls_without_logging_credentials(
    caplog, monkeypatch
) -> None:
    captured: dict[str, object] = {}

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            captured["connection"] = (host, port, timeout)

        def __enter__(self) -> FakeSMTP:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def starttls(self, *, context: object) -> None:
            captured["starttls"] = context is not None

        def login(self, username: str, password: str) -> None:
            captured["credentials"] = (username, password)

        def send_message(self, message: EmailMessage) -> None:
            captured["message"] = message

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "smtp-user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-secret")
    monkeypatch.setenv("SMTP_STARTTLS", "true")
    monkeypatch.setenv("EMAIL_FROM", "no-reply@example.com")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
    monkeypatch.setattr(email_delivery.smtplib, "SMTP", FakeSMTP)

    with caplog.at_level(logging.DEBUG):
        send_verification_email(
            recipient="person@example.com", token="synthetic-verification-token"
        )

    message = captured["message"]
    assert isinstance(message, EmailMessage)
    assert captured["connection"] == ("smtp.example.com", 587, 15)
    assert captured["starttls"] is True
    assert captured["credentials"] == ("smtp-user", "smtp-secret")
    assert message["To"] == "person@example.com"
    assert "https://api.example.com/api/v1/auth/verify-email" in message.get_content()
    assert "synthetic-verification-token" in message.get_content()
    assert "smtp-secret" not in caplog.text


def test_unknown_email_backend_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("EMAIL_BACKEND", "disabled")

    with pytest.raises(EmailDeliveryFailure, match="EMAIL_BACKEND"):
        send_verification_email(recipient="person@example.com", token="synthetic-token")
