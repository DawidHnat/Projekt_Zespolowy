"""SCRUM-87: shared append-only audit_events table and mutation-prevention trigger."""

import sqlalchemy as sa
from alembic import op

revision = "0016_audit_events"
down_revision = "0015_license_compatibility"


def upgrade():
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_account", sa.String(length=64), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_type", sa.String(length=20), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=True),
        sa.Column("operation", sa.String(length=60), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "actor_type IN ('user', 'import', 'system')",
            name="ck_audit_events_actor_type",
        ),
        sa.CheckConstraint(
            "entity_type IN ('vehicle', 'vehicle_odometer', 'vehicle_document', "
            "'driver', 'driver_assignment', 'trip_annotation', 'user_account', 'user_session')",
            name="ck_audit_events_entity_type",
        ),
        sa.CheckConstraint(
            "outcome IN ('succeeded', 'denied', 'failed')",
            name="ck_audit_events_outcome",
        ),
    )
    op.create_index("ix_audit_events_occurred_at", "audit_events", ["occurred_at"])
    op.create_index("ix_audit_events_source_account", "audit_events", ["source_account"])
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_vehicle_id", "audit_events", ["vehicle_id"])
    op.create_index("ix_audit_events_correlation_id", "audit_events", ["correlation_id"])
    op.create_index(
        "ix_audit_events_source_occurred",
        "audit_events",
        ["source_account", "occurred_at"],
    )
    op.create_index(
        "ix_audit_events_vehicle_occurred",
        "audit_events",
        ["vehicle_id", "occurred_at"],
    )

    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.execute(
            sa.text(
                """
                CREATE OR REPLACE FUNCTION prevent_audit_events_mutation()
                RETURNS trigger AS $$
                BEGIN
                    IF current_setting('fleet_flow.audit_maintenance', true) = 'allow' THEN
                        IF TG_OP = 'DELETE' THEN
                            RETURN OLD;
                        END IF;
                        RETURN NEW;
                    END IF;
                    RAISE EXCEPTION
                        'SCRUM-87: audit_events is append-only; UPDATE and DELETE are prohibited';
                END;
                $$ LANGUAGE plpgsql;
                """
            )
        )
        connection.execute(
            sa.text(
                """
                CREATE TRIGGER trg_audit_events_append_only
                BEFORE UPDATE OR DELETE ON audit_events
                FOR EACH ROW EXECUTE FUNCTION prevent_audit_events_mutation();
                """
            )
        )


def downgrade():
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.execute(
            sa.text("DROP TRIGGER IF EXISTS trg_audit_events_append_only ON audit_events")
        )
        connection.execute(sa.text("DROP FUNCTION IF EXISTS prevent_audit_events_mutation()"))
    op.drop_index("ix_audit_events_vehicle_occurred", table_name="audit_events")
    op.drop_index("ix_audit_events_source_occurred", table_name="audit_events")
    op.drop_index("ix_audit_events_correlation_id", table_name="audit_events")
    op.drop_index("ix_audit_events_vehicle_id", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_id", table_name="audit_events")
    op.drop_index("ix_audit_events_entity_type", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_id", table_name="audit_events")
    op.drop_index("ix_audit_events_source_account", table_name="audit_events")
    op.drop_index("ix_audit_events_occurred_at", table_name="audit_events")
    op.drop_table("audit_events")
