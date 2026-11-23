"""Join the account administration and trip history migration branches."""

revision = "0015_merge_accounts_and_trips"
down_revision = ("0014_merge_account_links", "0012_trip_history")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
