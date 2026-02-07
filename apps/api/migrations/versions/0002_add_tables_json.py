"""Add tables_json to techniques."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("techniques", sa.Column("tables_json", sa.JSON()))


def downgrade() -> None:
    op.drop_column("techniques", "tables_json")
