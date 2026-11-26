"""Add the extended manual vehicle card fields."""

import sqlalchemy as sa
from alembic import op

revision = "0012_vehicle_full_card"
down_revision = "0011_vehicle_card_ownership"


def upgrade():
    op.add_column("vehicles", sa.Column("ownership_category", sa.String(20)))
    op.add_column("vehicles", sa.Column("purchase_date", sa.Date()))
    op.add_column("vehicles", sa.Column("first_registration", sa.Date()))
    op.add_column("vehicles", sa.Column("first_registration_poland", sa.Date()))
    op.add_column("vehicles", sa.Column("fuel_type", sa.String(50)))
    op.add_column("vehicles", sa.Column("engine_capacity_cc", sa.Integer()))
    op.add_column("vehicles", sa.Column("power_kw", sa.Integer()))
    op.add_column("vehicles", sa.Column("dmc_kg", sa.Integer()))
    op.add_column("vehicles", sa.Column("curb_weight_kg", sa.Integer()))
    op.add_column("vehicles", sa.Column("payload_kg", sa.Integer()))
    op.add_column("vehicles", sa.Column("seats", sa.Integer()))
    op.add_column("vehicles", sa.Column("axles", sa.Integer()))

    op.create_check_constraint(
        "ck_vehicle_full_card_positive_numbers",
        "vehicles",
        "engine_capacity_cc IS NULL OR engine_capacity_cc > 0",
    )
    op.create_check_constraint(
        "ck_vehicle_full_card_weights",
        "vehicles",
        "(power_kw IS NULL OR power_kw >= 0) "
        "AND (dmc_kg IS NULL OR dmc_kg > 0) "
        "AND (curb_weight_kg IS NULL OR curb_weight_kg >= 0) "
        "AND (payload_kg IS NULL OR payload_kg >= 0)",
    )
    op.create_check_constraint(
        "ck_vehicle_full_card_capacity",
        "vehicles",
        "(seats IS NULL OR seats > 0) AND (axles IS NULL OR axles > 0)",
    )


def downgrade():
    op.drop_constraint("ck_vehicle_full_card_capacity", "vehicles", type_="check")
    op.drop_constraint("ck_vehicle_full_card_weights", "vehicles", type_="check")
    op.drop_constraint("ck_vehicle_full_card_positive_numbers", "vehicles", type_="check")
    for name in (
        "axles",
        "seats",
        "payload_kg",
        "curb_weight_kg",
        "dmc_kg",
        "power_kw",
        "engine_capacity_cc",
        "fuel_type",
        "first_registration_poland",
        "first_registration",
        "purchase_date",
        "ownership_category",
    ):
        op.drop_column("vehicles", name)
