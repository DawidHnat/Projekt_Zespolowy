"""Store pending profile email changes separately from recovery and activation."""

import sqlalchemy as sa
from alembic import op

revision = "0013_email_confirmation"
down_revision = "0012_account_administration"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_changes",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("new_email", sa.String(254), nullable=False),
        sa.Column("account_version", sa.Integer(), nullable=False),
    )
    op.create_index("ix_email_changes_user_id", "email_changes", ["user_id"])


def downgrade():
    op.drop_table("email_changes")
