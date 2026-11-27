"""SCRUM-58: private vehicle documents, shared vehicle photo version, and quarantine state."""

import sqlalchemy as sa
from alembic import op

revision = "0014_vehicle_documents"
down_revision = "0013_manual_vehicles"


def upgrade():
    op.add_column(
        "vehicles",
        sa.Column("photo_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        "ck_vehicles_photo_version",
        "vehicles",
        "photo_version >= 0",
    )
    op.create_table(
        "vehicle_attachments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("original_name", sa.String(120), nullable=False),
        sa.Column("mime_type", sa.String(50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(80), nullable=True, unique=True),
        sa.Column("scan_status", sa.String(30), nullable=False),
        sa.Column("scan_code", sa.String(60), nullable=True),
        sa.Column("width_px", sa.Integer(), nullable=True),
        sa.Column("height_px", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("uploaded_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('inspection', 'insurance', 'vehicle_photo')",
            name="ck_vehicle_attachments_kind",
        ),
        sa.CheckConstraint(
            "scan_status IN ('quarantined', 'clean', 'rejected', 'scanner_unavailable')",
            name="ck_vehicle_attachments_scan_status",
        ),
        sa.CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 52428800",
            name="ck_vehicle_attachments_size",
        ),
        sa.CheckConstraint("version >= 1", name="ck_vehicle_attachments_version"),
    )
    op.create_index(
        "ix_vehicle_attachments_vehicle_id",
        "vehicle_attachments",
        ["vehicle_id"],
    )


def downgrade():
    connection = op.get_bind()
    attachments_count = connection.scalar(sa.text("SELECT count(*) FROM vehicle_attachments"))
    photos_versioned = connection.scalar(
        sa.text("SELECT count(*) FROM vehicles WHERE photo_version > 0")
    )
    if attachments_count or photos_versioned:
        raise RuntimeError(
            "SCRUM-58: vehicle documents or photos exist and cannot be represented by old schema; "
            "keep schema and roll back application"
        )
    op.drop_index("ix_vehicle_attachments_vehicle_id", table_name="vehicle_attachments")
    op.drop_table("vehicle_attachments")
    op.drop_constraint("ck_vehicles_photo_version", "vehicles", type_="check")
    op.drop_column("vehicles", "photo_version")
