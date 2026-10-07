"""Create fleet snapshots and locally annotated trips."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(100), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("registration", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("odometer_km", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source IN ('demo', 'webfleet')", name="vehicles_source_valid"),
        sa.CheckConstraint(
            "status IN ('driving', 'parked', 'offline', 'unknown')", name="vehicles_status_valid"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicles_source_status", "vehicles", ["source", "status"])
    op.create_table(
        "trips",
        sa.Column("id", sa.String(100), nullable=False),
        sa.Column("vehicle_id", sa.String(100), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("start_address", sa.String(500), nullable=False),
        sa.Column("end_address", sa.String(500), nullable=False),
        sa.Column("purpose", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.CheckConstraint("source IN ('demo', 'webfleet')", name="trips_source_valid"),
        sa.CheckConstraint("distance_km >= 0", name="trips_distance_nonnegative"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trips_vehicle_started", "trips", ["vehicle_id", "started_at"])


def downgrade() -> None:
    op.drop_index("ix_trips_vehicle_started", table_name="trips")
    op.drop_table("trips")
    op.drop_index("ix_vehicles_source_status", table_name="vehicles")
    op.drop_table("vehicles")
