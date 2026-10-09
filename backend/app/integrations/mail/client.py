"""OVH SMTP authentication diagnostic. It never sends an email."""

import smtplib
import ssl

import certifi

from app.core.config import SmtpSettings


class SmtpError(Exception):
    pass


def check_smtp(settings: SmtpSettings) -> None:
    try:
        with smtplib.SMTP_SSL(
            settings.host,
            settings.port,
            timeout=settings.timeout_seconds,
            context=ssl.create_default_context(cafile=certifi.where()),
        ) as client:
            # smtplib debug mode exposes credentials and must remain disabled.
            client.login(settings.username, settings.password)
            status, _ = client.noop()
            if status != 250:
                raise SmtpError("SMTP: serwer nie potwierdził gotowości")
    except smtplib.SMTPAuthenticationError:
        raise SmtpError("SMTP: odrzucone logowanie; sprawdź skrzynkę i SMTP_PASSWORD") from None
    except (OSError, smtplib.SMTPException):
        raise SmtpError("SMTP: błąd połączenia lub TLS") from None
