import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"


def upgrade():
    op.create_table(
        "trips",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("external_uid", sa.String(200), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True)),
        sa.Column("distance_km", sa.Numeric(14, 3)),
        sa.UniqueConstraint("vehicle_id", "external_uid"),
        sa.CheckConstraint("end_at IS NULL OR end_at >= start_at", name="ck_trips_time_order"),
        sa.CheckConstraint(
            "distance_km IS NULL OR (distance_km >= 0 AND distance_km <= 99999999999.999)",
            name="ck_trips_distance",
        ),
    )
    op.create_index("ix_trips_vehicle_start", "trips", ["vehicle_id", "start_at"])
    op.create_table(
        "trip_annotations",
        sa.Column("trip_id", sa.Uuid(), sa.ForeignKey("trips.id"), primary_key=True),
        sa.Column("purpose", sa.String(200)),
        sa.Column("description", sa.String(2000)),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 2", name="ck_trip_annotations_version"),
    )


def downgrade():
    op.drop_table("trip_annotations")
    op.drop_index("ix_trips_vehicle_start", table_name="trips")
    op.drop_table("trips")
