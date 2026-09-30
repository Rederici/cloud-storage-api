"""rename user table to account

Revision ID: 45654fdf4438
Revises: 1bfa4d54ae72
Create Date: 2026-09-21 11:08:23.871261

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45654fdf4438"
down_revision: str | Sequence[str] | None = "1bfa4d54ae72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("user", "account")


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table("account", "user")
