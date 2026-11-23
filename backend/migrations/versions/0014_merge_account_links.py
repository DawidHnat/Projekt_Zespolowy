"""Join the email confirmation and login alias migration branches."""

revision = "0014_merge_account_links"
down_revision = ("0013_email_confirmation", "0013_email_login")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
