"""Emit the single prose fingerprint documented in this PR; fail closed on expiry."""

from datetime import UTC, date, datetime

FINGERPRINT = (
    "aee868abdc2979681fa1e113698e1bd4d473ebf0:"
    "docs/COURSE_AGENT_HANDOFFS.md:generic-api-key:22"
)
EXPIRES_ON = date(2026, 12, 18)


def ignore_file(today: date) -> str:
    if today >= EXPIRES_ON:
        raise ValueError(
            "Gitleaks prose exception expired; renew through independent review"
        )
    return FINGERPRINT + "\n"


if __name__ == "__main__":
    try:
        print(ignore_file(datetime.now(UTC).date()), end="")
    except ValueError as error:
        raise SystemExit(str(error)) from error
