"""Store imported trip facts, stops and completed report windows."""

import sqlalchemy as sa
from alembic import op

revision = "0012_trip_history"
down_revision = "0011_vehicle_card_ownership"


def upgrade():
    for field in ("start_address", "end_address"):
        op.add_column("trips", sa.Column(field, sa.String(500)))
    op.add_column("trips", sa.Column("driver_id", sa.Uuid()))
    op.create_foreign_key("fk_trip_driver", "trips", "drivers", ["driver_id"], ["id"])
    op.create_table(
        "trip_stops",
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id"), primary_key=True),
        sa.Column("start_at", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("address", sa.String(500)),
        sa.CheckConstraint("end_at >= start_at", name="ck_trip_stop_time_order"),
    )
    op.create_table(
        "trip_history_days",
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id"), primary_key=True),
        sa.Column("report_day", sa.Date(), primary_key=True),
        sa.Column("imported_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(80)),
    )
    op.create_table(
        "trip_history_sources",
        sa.Column("source_account", sa.String(64), primary_key=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("trip_history_sources")
    op.drop_table("trip_history_days")
    op.drop_table("trip_stops")
    op.drop_constraint("fk_trip_driver", "trips", type_="foreignkey")
    for field in ("driver_id", "end_address", "start_address"):
        op.drop_column("trips", field)
