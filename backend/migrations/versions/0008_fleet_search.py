"""Derived Unicode search values; source facts, IDs and manual driver fields stay intact."""

import sqlalchemy as sa
from alembic import op

revision = "0008_fleet_search"
down_revision = "0007"


def upgrade():
    for name, length in (
        ("search_name", 600),
        ("search_number", 600),
        ("search_license_plate", 300),
        ("search_make", 300),
        ("search_model", 300),
        ("search_vin", 300),
    ):
        op.add_column(
            "vehicles", sa.Column(name, sa.String(length), nullable=False, server_default="")
        )
    vehicles = sa.table(
        "vehicles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("number", sa.String()),
        sa.column("license_plate", sa.String()),
        sa.column("make", sa.String()),
        sa.column("model", sa.String()),
        sa.column("vin", sa.String()),
        sa.column("search_name", sa.String()),
        sa.column("search_number", sa.String()),
        sa.column("search_license_plate", sa.String()),
        sa.column("search_make", sa.String()),
        sa.column("search_model", sa.String()),
        sa.column("search_vin", sa.String()),
    )
    connection = op.get_bind()
    # Keyset batches bound application memory, including accounts larger than 10k.
    last_id = None
    while True:
        query = sa.select(
            vehicles.c.id,
            vehicles.c.name,
            vehicles.c.number,
            vehicles.c.license_plate,
            vehicles.c.make,
            vehicles.c.model,
            vehicles.c.vin,
        )
        if last_id is not None:
            query = query.where(vehicles.c.id > last_id)
        rows = connection.execute(query.order_by(vehicles.c.id).limit(500)).mappings().all()
        if not rows:
            break
        connection.execute(
            vehicles.update()
            .where(vehicles.c.id == sa.bindparam("row_id"))
            .values(
                search_name=sa.bindparam("fold_name"),
                search_number=sa.bindparam("fold_number"),
                search_license_plate=sa.bindparam("fold_plate"),
                search_make=sa.bindparam("fold_make"),
                search_model=sa.bindparam("fold_model"),
                search_vin=sa.bindparam("fold_vin"),
            ),
            [
                {
                    "row_id": row["id"],
                    "fold_name": row["name"].casefold(),
                    "fold_number": (row["number"] or "").casefold(),
                    "fold_plate": (row["license_plate"] or "").casefold(),
                    "fold_make": (row["make"] or "").casefold(),
                    "fold_model": (row["model"] or "").casefold(),
                    "fold_vin": (row["vin"] or "").casefold(),
                }
                for row in rows
            ],
        )
        last_id = rows[-1]["id"]


def downgrade():
    for name in (
        "search_vin",
        "search_model",
        "search_make",
        "search_license_plate",
        "search_number",
        "search_name",
    ):
        op.drop_column("vehicles", name)
