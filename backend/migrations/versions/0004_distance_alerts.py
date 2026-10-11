import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"


def upgrade():
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_account", sa.String(64), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("threshold_km", sa.Numeric(14, 1), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id")),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("threshold_km > 0", name="ck_alert_rules_positive_threshold"),
        sa.CheckConstraint(
            "type = 'daily_distance_threshold'", name="ck_alert_rules_supported_type"
        ),
    )
    op.create_index("ix_alert_rules_source_account", "alert_rules", ["source_account"])
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("rule_id", sa.Uuid(), sa.ForeignKey("alert_rules.id"), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("event_day", sa.Date(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("threshold_km", sa.Numeric(14, 1), nullable=False),
        sa.Column("distance_km", sa.Numeric(14, 1), nullable=False),
        sa.UniqueConstraint("rule_id", "vehicle_id", "event_day"),
    )
    op.create_index("ix_alerts_rule_id", "alerts", ["rule_id"])
    op.create_table(
        "daily_distances",
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("vehicles.id"), primary_key=True),
        sa.Column("event_day", sa.Date(), primary_key=True),
        sa.Column("distance_km", sa.Numeric(14, 1), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("distance_km >= 0", name="ck_daily_distances_nonnegative"),
    )
    op.create_table(
        "alert_receipts",
        sa.Column("alert_id", sa.Uuid(), sa.ForeignKey("alerts.id"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("alert_receipts")
    op.drop_table("daily_distances")
    op.drop_table("alerts")
    op.drop_table("alert_rules")
