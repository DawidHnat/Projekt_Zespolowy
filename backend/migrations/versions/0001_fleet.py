"""Fleet foundation. Local driver fields are deliberately separate."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None


def upgrade():
    op.create_table(
        "drivers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_account", sa.String(64), nullable=False),
        sa.Column("external_uid", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("number", sa.String(200)),
        sa.Column("license_plate", sa.String(100)),
        sa.Column("vehicle_type", sa.String(100)),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), sa.ForeignKey("drivers.id")),
        sa.UniqueConstraint("source_account", "external_uid"),
    )
    op.create_index("ix_vehicles_source_account", "vehicles", ["source_account"])
    op.create_table(
        "measurements",
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id"), primary_key=True),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("odometer_km", sa.Numeric(14, 1)),
        sa.Column("ignition_on", sa.Boolean()),
        sa.Column("standing_still", sa.Boolean()),
        sa.Column("gps_quality", sa.String(1)),
        sa.Column("position_at", sa.DateTime(timezone=True)),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "sync_states",
        sa.Column("source_account", sa.String(64), primary_key=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(80)),
    )


def downgrade():
    op.drop_table("sync_states")
    op.drop_table("measurements")
    op.drop_table("vehicles")
    op.drop_table("drivers")
