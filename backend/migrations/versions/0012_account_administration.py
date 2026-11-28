"""Extend legacy users with account states and separate activation links."""

import sqlalchemy as sa
from alembic import op

revision = "0012_account_administration"
down_revision = "0011_vehicle_card_ownership"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("first_name", sa.String(60)))
    op.add_column("users", sa.Column("last_name", sa.String(60)))
    op.add_column("users", sa.Column("disabled_state", sa.String(10)))
    op.add_column(
        "users",
        sa.Column("needs_activation", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("users", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.create_check_constraint(
        "ck_users_access_state",
        "users",
        "(NOT needs_activation OR NOT active) AND "
        "(disabled_state IS NULL OR "
        "(NOT active AND (disabled_state = 'blocked' OR "
        "(disabled_state = 'pending' AND needs_activation))))",
    )
    op.create_check_constraint("ck_users_version", "users", "version >= 1")
    op.create_table(
        "account_activations",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_account_activations_user_id", "account_activations", ["user_id"])


def downgrade():
    op.drop_table("account_activations")
    op.drop_constraint("ck_users_version", "users", type_="check")
    op.drop_constraint("ck_users_access_state", "users", type_="check")
    op.drop_column("users", "version")
    op.drop_column("users", "needs_activation")
    op.drop_column("users", "disabled_state")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
