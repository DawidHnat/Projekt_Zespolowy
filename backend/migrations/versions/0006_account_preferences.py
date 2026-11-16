import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade():
    op.create_table(
        "account_preferences",
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("module", sa.String(40), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_account_preferences_version"),
        sa.CheckConstraint(
            "module IN ('dashboard', 'vehicles')", name="ck_account_preferences_module"
        ),
    )


def downgrade():
    op.drop_table("account_preferences")
