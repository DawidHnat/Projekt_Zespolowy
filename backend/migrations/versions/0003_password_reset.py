import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade():
    op.add_column("users", sa.Column("email", sa.String(254)))
    op.create_table(
        "password_resets",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_password_resets_user_id", "password_resets", ["user_id"])


def downgrade():
    op.drop_table("password_resets")
    op.drop_column("users", "email")
