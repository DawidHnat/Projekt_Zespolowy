"""Preserve legacy vehicle corrections and track new corrections per field."""

import sqlalchemy as sa
from alembic import op

revision = "0011_vehicle_card_ownership"
down_revision = "0010_manual_drivers"

MANUAL_FIELDS = ("manual_name", "manual_license_plate", "manual_vehicle_type")


def upgrade():
    for name in MANUAL_FIELDS:
        op.add_column(
            "vehicles", sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.false())
        )
    op.add_column(
        "vehicles", sa.Column("card_version", sa.Integer(), nullable=False, server_default="1")
    )
    vehicles = sa.table(
        "vehicles",
        sa.column("locally_edited", sa.Boolean()),
        *(sa.column(name, sa.Boolean()) for name in MANUAL_FIELDS),
    )
    # The legacy flag cannot tell us which shared field the user edited.
    op.execute(
        vehicles.update()
        .where(vehicles.c.locally_edited.is_(True))
        .values({name: True for name in MANUAL_FIELDS})
    )


def downgrade():
    # The old application can still preserve vehicle values via locally_edited.
    op.drop_column("vehicles", "card_version")
    for name in reversed(MANUAL_FIELDS):
        op.drop_column("vehicles", name)
