"""SCRUM-70: vehicle DMC/seat/trailer/category requirements and trip driver selection."""

import sqlalchemy as sa
from alembic import op

revision = "0015_license_compatibility"
down_revision = "0014_vehicle_documents"

CATEGORIES_SQL = (
    "('AM','A1','A2','A','B1','B','B+E','C1','C1+E','C','C+E','D1','D1+E','D','D+E','T')"
)


def upgrade():
    op.add_column("vehicles", sa.Column("gross_weight_kg", sa.Integer(), nullable=True))
    op.add_column("vehicles", sa.Column("passenger_seats", sa.Integer(), nullable=True))
    op.add_column(
        "vehicles",
        sa.Column("tows_heavy_trailer", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "vehicles",
        sa.Column("required_category_override", sa.String(5), nullable=True),
    )
    op.create_check_constraint(
        "ck_vehicles_gross_weight_kg",
        "vehicles",
        "gross_weight_kg IS NULL OR (gross_weight_kg > 0 AND gross_weight_kg <= 120000)",
    )
    op.create_check_constraint(
        "ck_vehicles_passenger_seats",
        "vehicles",
        "passenger_seats IS NULL OR (passenger_seats >= 0 AND passenger_seats <= 120)",
    )
    op.create_check_constraint(
        "ck_vehicles_req_cat_override",
        "vehicles",
        f"required_category_override IS NULL OR required_category_override IN {CATEGORIES_SQL}",
    )
    op.add_column(
        "trip_annotations",
        sa.Column("driver_id", sa.Uuid(), sa.ForeignKey("drivers.id"), nullable=True),
    )
    op.create_index("ix_trip_annotations_driver_id", "trip_annotations", ["driver_id"])


def downgrade():
    connection = op.get_bind()
    vehicle_rules_used = connection.scalar(
        sa.text(
            "SELECT count(*) FROM vehicles WHERE gross_weight_kg IS NOT NULL "
            "OR passenger_seats IS NOT NULL OR tows_heavy_trailer IS TRUE "
            "OR required_category_override IS NOT NULL"
        )
    )
    trip_drivers_used = connection.scalar(
        sa.text("SELECT count(*) FROM trip_annotations WHERE driver_id IS NOT NULL")
    )
    if vehicle_rules_used or trip_drivers_used:
        raise RuntimeError(
            "SCRUM-70: vehicle license requirements or trip drivers exist and cannot be "
            "represented by old schema; keep schema and roll back application"
        )
    op.drop_index("ix_trip_annotations_driver_id", table_name="trip_annotations")
    op.drop_column("trip_annotations", "driver_id")
    op.drop_constraint("ck_vehicles_req_cat_override", "vehicles", type_="check")
    op.drop_constraint("ck_vehicles_passenger_seats", "vehicles", type_="check")
    op.drop_constraint("ck_vehicles_gross_weight_kg", "vehicles", type_="check")
    for column in (
        "required_category_override",
        "tows_heavy_trailer",
        "passenger_seats",
        "gross_weight_kg",
    ):
        op.drop_column("vehicles", column)
