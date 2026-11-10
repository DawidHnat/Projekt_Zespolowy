import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade():
    op.add_column("vehicles", sa.Column("make", sa.String(100)))
    op.add_column("vehicles", sa.Column("model", sa.String(100)))
    op.add_column("vehicles", sa.Column("year", sa.Integer()))
    op.add_column("vehicles", sa.Column("vin", sa.String(100)))
    op.add_column(
        "vehicles",
        sa.Column("locally_edited", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("measurements", sa.Column("speed_kmh", sa.Numeric(6, 1)))
    op.add_column("measurements", sa.Column("position_address", sa.String(500)))


def downgrade():
    op.drop_column("measurements", "position_address")
    op.drop_column("measurements", "speed_kmh")
    op.drop_column("vehicles", "locally_edited")
    op.drop_column("vehicles", "vin")
    op.drop_column("vehicles", "year")
    op.drop_column("vehicles", "model")
    op.drop_column("vehicles", "make")
