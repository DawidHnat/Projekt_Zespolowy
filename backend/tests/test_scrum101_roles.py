from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.models import SyncState
from app.modules.auth.models import User
from app.modules.fleet.sync import account_key

ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        ("admin", 404),
        ("editor", 404),
        ("viewer", 403),
    ],
)
def test_vehicle_edit_requires_editor_role(application, role, expected_status):
    app, client = application

    with app.state.sessions() as session:
        user = session.scalar(select(User).where(User.username == "test-user"))
        user.role = role
        session.add(
            SyncState(
                source_account=account_key(app.state.settings.webfleet_account),
                last_success_at=datetime.now(UTC),
            )
        )
        session.commit()

    response = client.post(
        "/api/v1/auth/login",
        headers=ORIGIN,
        json={
            "username": "test-user",
            "password": "synthetic-test-password",
        },
    )
    assert response.status_code == 200

    result = client.patch(
        f"/api/v1/fleet/vehicles/{uuid4()}",
        headers=ORIGIN,
        json={"name": "Synthetic test vehicle"},
    )

    assert result.status_code == expected_status
