"""Manual profiles and many-to-many assignments; never infer missing names or dates."""

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "0008_manual_drivers"
down_revision = "0007_user_roles"
branch_labels = None
depends_on = None


def upgrade():
    for column in (
        sa.Column("source_account", sa.String(64)),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("identifier", sa.String(100)),
        sa.Column("identifier_key", sa.String(300)),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(254)),
        sa.Column("search_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    ):
        op.add_column("drivers", column)
    op.alter_column("drivers", "display_name", type_=sa.String(201))
    op.create_index("ix_drivers_source_account", "drivers", ["source_account"])
    op.create_unique_constraint(
        "uq_driver_identifier", "drivers", ["source_account", "identifier_key"]
    )
    op.create_check_constraint("ck_driver_version", "drivers", "version >= 1")
    assignments = op.create_table(
        "driver_assignments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("driver_id", sa.Uuid(), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at",
            name="ck_driver_assignment_dates",
        ),
        sa.CheckConstraint("NOT active OR ended_at IS NULL", name="ck_driver_assignment_active"),
    )
    op.create_index("ix_driver_assignments_vehicle", "driver_assignments", ["vehicle_id"])
    op.create_index("ix_driver_assignments_driver", "driver_assignments", ["driver_id"])
    op.create_index(
        "uq_driver_assignments_open_pair",
        "driver_assignments",
        ["driver_id", "vehicle_id"],
        unique=True,
        postgresql_where=sa.text("active"),
    )
    op.create_table(
        "driver_categories",
        sa.Column("driver_id", sa.Uuid(), sa.ForeignKey("drivers.id"), primary_key=True),
        sa.Column("category", sa.String(5), primary_key=True),
    )
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE drivers SET source_account = s.source FROM "
            "(SELECT driver_id, min(source_account) AS source FROM vehicles "
            "WHERE driver_id IS NOT NULL GROUP BY driver_id "
            "HAVING count(DISTINCT source_account) = 1) s WHERE drivers.id = s.driver_id"
        )
    )
    # Keyset batches preserve UUID and display_name without guessing first/last name.
    previous = None
    while True:
        rows = (
            connection.execute(
                sa.text(
                    "SELECT id, display_name FROM drivers "
                    + ("WHERE id > :previous " if previous else "")
                    + "ORDER BY id LIMIT 500"
                ),
                {"previous": previous} if previous else {},
            )
            .mappings()
            .all()
        )
        if not rows:
            break
        for row in rows:
            connection.execute(
                sa.text("UPDATE drivers SET search_text=:value WHERE id=:id"),
                {"value": row["display_name"].casefold(), "id": row["id"]},
            )
        previous = rows[-1]["id"]
    recorded = datetime.now(UTC)
    previous = None
    while True:
        rows = (
            connection.execute(
                sa.text(
                    "SELECT v.id AS vehicle_id, d.id AS driver_id, d.active FROM vehicles v "
                    "JOIN drivers d ON d.id=v.driver_id "
                    + ("WHERE v.id > :previous " if previous else "")
                    + "ORDER BY v.id LIMIT 500"
                ),
                {"previous": previous} if previous else {},
            )
            .mappings()
            .all()
        )
        if not rows:
            break
        connection.execute(
            assignments.insert(),
            [
                {
                    "id": uuid4(),
                    "driver_id": row["driver_id"],
                    "vehicle_id": row["vehicle_id"],
                    "active": row["active"],
                    "started_at": None,
                    "ended_at": None,
                    "recorded_at": recorded,
                }
                for row in rows
            ],
        )
        previous = rows[-1]["vehicle_id"]


def downgrade():
    connection = op.get_bind()
    # A rollback must not silently discard manual profiles or assignment history.
    expanded = connection.scalar(
        sa.text(
            "SELECT (SELECT count(*) FROM drivers "
            "WHERE first_name IS NOT NULL OR last_name IS NOT NULL "
            "OR identifier IS NOT NULL OR phone IS NOT NULL OR email IS NOT NULL OR version > 1 "
            "OR length(display_name)>120) + (SELECT count(*) FROM driver_categories) + "
            "(SELECT count(*) FROM driver_assignments a LEFT JOIN vehicles v ON v.id=a.vehicle_id "
            "WHERE a.started_at IS NOT NULL OR a.ended_at IS NOT NULL "
            "OR v.driver_id IS DISTINCT FROM a.driver_id)"
        )
    )
    if expanded:
        raise RuntimeError(
            "SCRUM-52: manual data cannot be represented by old schema; "
            "keep schema and roll back application"
        )
    op.drop_table("driver_categories")
    op.drop_table("driver_assignments")
    op.drop_constraint("ck_driver_version", "drivers", type_="check")
    op.drop_constraint("uq_driver_identifier", "drivers", type_="unique")
    op.drop_index("ix_drivers_source_account", table_name="drivers")
    op.alter_column("drivers", "display_name", type_=sa.String(120))
    for column in (
        "source_account",
        "first_name",
        "last_name",
        "identifier",
        "identifier_key",
        "phone",
        "email",
        "search_text",
        "version",
    ):
        op.drop_column("drivers", column)
