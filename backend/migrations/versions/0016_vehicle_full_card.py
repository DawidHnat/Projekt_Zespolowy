"""SCRUM-68: ownership category, leasing buyout and technical vehicle card data.

Fuel, leasing contract, DMC and passenger seats already exist (0013, 0015); this
revision only adds the remaining card fields and never duplicates those columns.
"""

import sqlalchemy as sa
from alembic import op

revision = "0016_vehicle_full_card"
down_revision = "0015_license_compatibility"

COLUMNS = (
    ("ownership_category", sa.String(20)),
    ("leasing_buyout_on", sa.Date()),
    ("first_registration_on", sa.Date()),
    ("first_registration_pl_on", sa.Date()),
    ("engine_capacity_cc", sa.Integer()),
    ("power_kw", sa.Integer()),
    ("curb_weight_kg", sa.Integer()),
    ("payload_kg", sa.Integer()),
    ("axles", sa.Integer()),
)

CONSTRAINTS = (
    (
        "ck_vehicles_ownership_category",
        "ownership_category IS NULL OR ownership_category IN ('Firmowe','Prywatne','Leasing')",
    ),
    (
        "ck_vehicles_card_technical",
        "(engine_capacity_cc IS NULL "
        "OR (engine_capacity_cc > 0 AND engine_capacity_cc <= 100000)) "
        "AND (power_kw IS NULL OR (power_kw > 0 AND power_kw <= 10000)) "
        "AND (curb_weight_kg IS NULL OR (curb_weight_kg > 0 AND curb_weight_kg <= 120000)) "
        "AND (payload_kg IS NULL OR (payload_kg > 0 AND payload_kg <= 120000)) "
        "AND (axles IS NULL OR (axles > 0 AND axles <= 20))",
    ),
    (
        "ck_vehicles_first_registration_order",
        "first_registration_on IS NULL OR first_registration_pl_on IS NULL "
        "OR first_registration_pl_on >= first_registration_on",
    ),
)


def upgrade():
    for name, column_type in COLUMNS:
        op.add_column("vehicles", sa.Column(name, column_type, nullable=True))
    for name, condition in CONSTRAINTS:
        op.create_check_constraint(name, "vehicles", condition)


def downgrade():
    connection = op.get_bind()
    filled = " OR ".join(f"{name} IS NOT NULL" for name, _ in COLUMNS)
    if connection.scalar(sa.text(f"SELECT count(*) FROM vehicles WHERE {filled}")):
        raise RuntimeError(
            "SCRUM-68: vehicle card data exists and cannot be represented by the 0015 schema; "
            "keep the schema and roll back only the application"
        )
    for name, _ in reversed(CONSTRAINTS):
        op.drop_constraint(name, "vehicles", type_="check")
    for name, _ in reversed(COLUMNS):
        op.drop_column("vehicles", name)
