"""SCRUM-24: mark annotated trips that a later complete report no longer lists.

0012_trip_history is already deployed from main, so the column is added here.
"""

import sqlalchemy as sa
from alembic import op

revision = "0016_trip_withdrawn"
down_revision = "0015_merge_accounts_and_trips"


def upgrade():
    op.add_column("trips", sa.Column("withdrawn_at", sa.DateTime(timezone=True)))


def downgrade():
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        # Lock before checking so a concurrent import is either seen or waits.
        op.execute("LOCK TABLE trips IN ACCESS EXCLUSIVE MODE")
    if connection.scalar(sa.text("SELECT count(*) FROM trips WHERE withdrawn_at IS NOT NULL")):
        raise RuntimeError(
            "SCRUM-24: trips marked as withdrawn exist and cannot be represented by the "
            "previous schema; keep the schema and roll back only the application"
        )
    op.drop_column("trips", "withdrawn_at")
