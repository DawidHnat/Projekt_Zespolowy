"""OVH SMTP: authentication diagnostics and account notifications."""

import smtplib
import ssl
from email.message import EmailMessage

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


def send_password_reset(settings: SmtpSettings, recipient: str, url: str) -> None:
    message = EmailMessage()
    message["From"] = settings.username
    message["To"] = recipient
    message["Subject"] = "Fleet-Flow — reset hasła"
    message.set_content(
        "Aby ustawić nowe hasło Fleet-Flow, otwórz poniższy link. "
        "Jest ważny 20 minut i działa jeden raz.\n\n"
        + url
        + "\n\nJeśli nie prosisz o zmianę hasła, zignoruj tę wiadomość."
    )
    _send(settings, recipient, message)


def send_password_changed(settings: SmtpSettings, recipient: str) -> None:
    message = EmailMessage()
    message["From"] = settings.username
    message["To"] = recipient
    message["Subject"] = "Fleet-Flow — zmieniono hasło"
    message.set_content(
        "Hasło Twojego konta Fleet-Flow zostało zmienione. "
        "Poprzednie sesje zostały wylogowane. "
        "Jeżeli nie wykonujesz tej zmiany, skontaktuj się z administratorem zespołu."
    )
    _send(settings, recipient, message)


def _send(settings: SmtpSettings, recipient: str, message: EmailMessage) -> None:
    try:
        with smtplib.SMTP_SSL(
            settings.host,
            settings.port,
            timeout=settings.timeout_seconds,
            context=ssl.create_default_context(cafile=certifi.where()),
        ) as client:
            client.login(settings.username, settings.password)
            client.send_message(message, from_addr=settings.username, to_addrs=[recipient])
    except (OSError, smtplib.SMTPException):
        raise SmtpError("SMTP: wiadomość nie została wysłana") from None
