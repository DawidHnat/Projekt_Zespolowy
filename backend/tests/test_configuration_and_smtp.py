import smtplib
import ssl
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import ConfigurationError, SmtpSettings, WebfleetSettings, load_environment
from app.integrations.mail.client import SmtpError, check_smtp


def test_secrets_are_loaded_literally_and_environment_has_priority(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("WEBFLEET_PASSWORD='literal${NOT_EXPANDED}'\nWEBFLEET_ACCOUNT=file\n")
    monkeypatch.setenv("WEBFLEET_ACCOUNT", "environment")
    monkeypatch.delenv("WEBFLEET_PASSWORD", raising=False)
    values = load_environment(path)
    assert values["WEBFLEET_PASSWORD"] == "literal${NOT_EXPANDED}"
    assert values["WEBFLEET_ACCOUNT"] == "environment"


def test_settings_repr_and_missing_errors_hide_values():
    settings = WebfleetSettings("private-account", "private-user", "private-pwd", "private-key")
    assert "private" not in repr(settings)
    with pytest.raises(ConfigurationError) as error:
        WebfleetSettings.from_environment({"WEBFLEET_ACCOUNT": "private-account"})
    assert "WEBFLEET_PASSWORD" in str(error.value)
    assert "private-account" not in str(error.value)


def test_explicit_missing_env_file_is_not_silently_replaced_with_process_settings(tmp_path):
    with pytest.raises(ConfigurationError, match="--env-file"):
        load_environment(tmp_path / "missing.env")


@pytest.mark.parametrize("timeout", ["NaN", "Infinity", "0", "121", "password-not-a-number"])
def test_invalid_timeout_is_rejected_without_exposing_value(timeout):
    with pytest.raises(ConfigurationError) as error:
        WebfleetSettings.from_environment(
            {
                "WEBFLEET_ACCOUNT": "a",
                "WEBFLEET_USERNAME": "u",
                "WEBFLEET_PASSWORD": "p",
                "WEBFLEET_API_KEY": "k",
                "WEBFLEET_TIMEOUT_SECONDS": timeout,
            }
        )
    assert "password-not-a-number" not in str(error.value)


def test_smtp_missing_credentials_do_not_attempt_connection():
    with patch("smtplib.SMTP_SSL") as connect:
        with pytest.raises(ConfigurationError, match="SMTP_PASSWORD"):
            SmtpSettings.from_environment({"SMTP_USERNAME": "test@example.invalid"})
    connect.assert_not_called()


@pytest.mark.parametrize("overrides", [{"SMTP_PORT": "25"}, {"SMTP_HOST": "unknown.example"}])
def test_smtp_only_supports_verified_ovh_tls_configuration(overrides):
    with pytest.raises(ConfigurationError):
        SmtpSettings.from_environment(
            {
                "SMTP_USERNAME": "test@example.invalid",
                "SMTP_PASSWORD": "secret",
                **overrides,
            }
        )


def test_smtp_login_uses_tls_and_never_sends_a_message():
    settings = SmtpSettings("test@example.invalid", "secret")
    assert "secret" not in repr(settings)
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.noop.return_value = (250, b"ok")
    with patch("smtplib.SMTP_SSL", return_value=connection) as connect:
        check_smtp(settings)
    context = connect.call_args.kwargs["context"]
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    connection.login.assert_called_once_with(settings.username, settings.password)
    connection.sendmail.assert_not_called()
    connection.send_message.assert_not_called()
    connection.set_debuglevel.assert_not_called()


def test_smtp_authentication_error_is_sanitized():
    with patch("smtplib.SMTP_SSL", side_effect=smtplib.SMTPAuthenticationError(535, b"secret")):
        with pytest.raises(SmtpError) as error:
            check_smtp(SmtpSettings("test@example.invalid", "secret"))
    assert "secret" not in str(error.value)
