"""Join the full vehicle card and audit history migration branches."""

revision = "0017_merge_vehicle_audit"
down_revision = ("0016_vehicle_full_card", "0016_audit_events")


def upgrade():
    pass


def downgrade():
    pass
