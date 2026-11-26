"""SCRUM-85: manual vehicles without WEBFLEET locator, extended card fields and dated odometer."""

import sqlalchemy as sa
from alembic import op

revision = "0013_manual_vehicles"
down_revision = "0012_vehicle_archive"


def upgrade():
    op.alter_column("vehicles", "external_uid", existing_type=sa.String(200), nullable=True)
    op.add_column(
        "vehicles",
        sa.Column("is_manual", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("vehicles", sa.Column("fuel_type", sa.String(50)))
    op.add_column("vehicles", sa.Column("leasing_company", sa.String(200)))
    op.add_column("vehicles", sa.Column("leasing_contract_no", sa.String(100)))
    op.add_column("vehicles", sa.Column("leasing_end_on", sa.Date()))
    op.add_column("vehicles", sa.Column("inspection_due_on", sa.Date()))
    op.add_column("vehicles", sa.Column("insurance_due_on", sa.Date()))
    op.add_column("vehicles", sa.Column("manual_odometer_km", sa.Numeric(14, 1)))
    op.add_column("vehicles", sa.Column("manual_odometer_date", sa.Date()))
    op.add_column("vehicles", sa.Column("manual_plate_key", sa.String(300)))
    op.add_column("vehicles", sa.Column("manual_vin_key", sa.String(300)))
    op.create_unique_constraint(
        "uq_vehicles_manual_plate_key",
        "vehicles",
        ["source_account", "manual_plate_key"],
    )
    op.create_unique_constraint(
        "uq_vehicles_manual_vin_key",
        "vehicles",
        ["source_account", "manual_vin_key"],
    )
    op.create_check_constraint(
        "ck_vehicles_origin_uid",
        "vehicles",
        "(is_manual AND external_uid IS NULL) OR (NOT is_manual AND external_uid IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_vehicles_manual_odometer",
        "vehicles",
        "(manual_odometer_km IS NULL AND manual_odometer_date IS NULL) "
        "OR (manual_odometer_km IS NOT NULL AND manual_odometer_km >= 0 "
        "AND manual_odometer_km <= 9999999.9 AND manual_odometer_date IS NOT NULL)",
    )


def downgrade():
    connection = op.get_bind()
    manual_or_extended = connection.scalar(
        sa.text(
            "SELECT count(*) FROM vehicles WHERE is_manual IS TRUE "
            "OR fuel_type IS NOT NULL OR leasing_company IS NOT NULL "
            "OR leasing_contract_no IS NOT NULL OR leasing_end_on IS NOT NULL "
            "OR inspection_due_on IS NOT NULL OR insurance_due_on IS NOT NULL "
            "OR manual_odometer_km IS NOT NULL OR manual_odometer_date IS NOT NULL"
        )
    )
    if manual_or_extended:
        raise RuntimeError(
            "SCRUM-85: manual vehicles or extended card data cannot be represented by 0012 schema, "
            "and pre-SCRUM-85 sync treats active manual vehicles (external_uid IS NULL) as "
            "INCOMPLETE_REPORT; do not downgrade schema or roll back app below SCRUM-85 while "
            "active manual vehicles exist — deploy a forward fix on 0013+ "
            "(see infra/deploy/README.md)"
        )
    op.drop_constraint("ck_vehicles_manual_odometer", "vehicles", type_="check")
    op.drop_constraint("ck_vehicles_origin_uid", "vehicles", type_="check")
    op.drop_constraint("uq_vehicles_manual_vin_key", "vehicles", type_="unique")
    op.drop_constraint("uq_vehicles_manual_plate_key", "vehicles", type_="unique")
    for column in (
        "manual_vin_key",
        "manual_plate_key",
        "manual_odometer_date",
        "manual_odometer_km",
        "insurance_due_on",
        "inspection_due_on",
        "leasing_end_on",
        "leasing_contract_no",
        "leasing_company",
        "fuel_type",
        "is_manual",
    ):
        op.drop_column("vehicles", column)
    op.alter_column("vehicles", "external_uid", existing_type=sa.String(200), nullable=False)
