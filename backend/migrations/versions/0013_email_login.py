"""Normalize login aliases from existing emails without modifying mailbox addresses."""

import sqlalchemy as sa
from alembic import op

revision = "0013_email_login"
down_revision = "0012_account_administration"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email_identifier", sa.String(508)))
    users = sa.table(
        "users",
        sa.column("id", sa.Uuid()),
        sa.column("email", sa.String(254)),
        sa.column("email_identifier", sa.String(508)),
    )
    connection = op.get_bind()
    accounts = connection.execute(
        sa.select(users.c.id, users.c.email).where(users.c.email.is_not(None))
    ).all()
    if accounts:
        connection.execute(
            users.update()
            .where(users.c.id == sa.bindparam("account_id"))
            .values(email_identifier=sa.bindparam("identifier")),
            [
                {"account_id": row.id, "identifier": row.email.strip().lower() or None}
                for row in accounts
            ],
        )
    # Legacy duplicates remain ambiguous until an administrator corrects their addresses.
    op.create_index("ix_users_email_identifier", "users", ["email_identifier"])


def downgrade():
    op.drop_index("ix_users_email_identifier", table_name="users")
    op.drop_column("users", "email_identifier")
