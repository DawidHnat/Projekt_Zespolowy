import sqlalchemy as sa
from alembic import op

revision = "0012_account_background_images"
down_revision = "0011_vehicle_card_ownership"


def upgrade():
    op.create_table(
        "account_background_images",
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("image_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("image", sa.LargeBinary(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(image) <= 8388608", name="ck_account_background_image_size"),
    )


def downgrade():
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        # Lock before checking so a concurrent upload is either seen or waits.
        op.execute("LOCK TABLE account_background_images IN ACCESS EXCLUSIVE MODE")
    if connection.scalar(sa.text("SELECT count(*) FROM account_background_images")):
        raise RuntimeError(
            "SCRUM-148: account backgrounds exist and cannot be represented by the 0011 "
            "schema; keep the schema and roll back only the application"
        )
    op.drop_table("account_background_images")
