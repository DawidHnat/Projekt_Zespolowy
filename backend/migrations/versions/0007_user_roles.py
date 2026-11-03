"""Constrain existing roles without silently rewriting user permissions."""

import sqlalchemy as sa
from alembic import op

revision = "0007_user_roles"
down_revision = "0006_fleet_search"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    connection.execute(sa.text("LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE"))
    # Avoid PostgreSQL's failing-row DETAIL exposing account data on a dirty upgrade.
    invalid = connection.scalar(
        sa.text(
            "SELECT count(*) FROM users "
            "WHERE role NOT IN ('admin', 'editor', 'viewer') OR role IS NULL"
        )
    )
    if invalid:
        raise RuntimeError("SCRUM-103: invalid existing roles; operator review required")
    op.create_check_constraint("ck_users_role", "users", "role IN ('admin', 'editor', 'viewer')")


def downgrade():
    op.drop_constraint("ck_users_role", "users", type_="check")
