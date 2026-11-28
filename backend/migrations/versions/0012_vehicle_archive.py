"""Add separate user archive state for vehicles without discarding history."""

import sqlalchemy as sa
from alembic import op

revision = "0012_vehicle_archive"
down_revision = "0011_vehicle_card_ownership"


def upgrade():
    op.add_column(
        "vehicles",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("vehicles", sa.Column("archived_at", sa.DateTime(timezone=True)))
    op.add_column(
        "vehicles",
        sa.Column("archived_by", sa.Uuid(), sa.ForeignKey("users.id")),
    )
    op.add_column("vehicles", sa.Column("archived_reason", sa.String(500)))
    op.create_check_constraint(
        "ck_vehicles_archive_state",
        "vehicles",
        "(NOT archived AND archived_at IS NULL AND archived_by IS NULL "
        "AND archived_reason IS NULL) OR (archived AND archived_at IS NOT NULL)",
    )


def downgrade():
    connection = op.get_bind()
    archived_count = connection.scalar(
        sa.text("SELECT count(*) FROM vehicles WHERE archived IS TRUE")
    )
    if archived_count:
        raise RuntimeError(
            "SCRUM-88: archived vehicles cannot be represented by old schema; "
            "keep schema and roll back application"
        )
    op.drop_constraint("ck_vehicles_archive_state", "vehicles", type_="check")
    op.drop_column("vehicles", "archived_reason")
    op.drop_column("vehicles", "archived_by")
    op.drop_column("vehicles", "archived_at")
    op.drop_column("vehicles", "archived")
