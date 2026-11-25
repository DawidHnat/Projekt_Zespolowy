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
            "SCRUM-85: manual vehicles or extended card data cannot be represented by old schema; "
            "keep schema and roll back application"
        )
    op.drop_constraint("ck_vehicles_manual_odometer", "vehicles", type_="check")
    op.drop_constraint("ck_vehicles_origin_uid", "vehicles", type_="check")
    for column in (
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
