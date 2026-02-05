"""Create the v0 schema cut line."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "studies",
        sa.Column("study_id", sa.String(), primary_key=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("venue", sa.Text(), nullable=False),
        sa.Column("study_type", sa.String(), nullable=False),
    )

    op.create_table(
        "outcomes",
        sa.Column("study_id", sa.String(), sa.ForeignKey("studies.study_id"), primary_key=True),
        sa.Column("outcome_id", sa.String(), primary_key=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
    )

    op.create_table(
        "results",
        sa.Column("study_id", sa.String(), sa.ForeignKey("studies.study_id"), primary_key=True),
        sa.Column("result_id", sa.String(), primary_key=True),
        sa.Column("outcome_id", sa.String(), nullable=False),
        sa.Column("result_label", sa.Text(), nullable=False),
        sa.Column("result_description", sa.Text()),
        sa.Column("effect_type", sa.String(), nullable=False),
        sa.Column("effect_value", sa.Float(), nullable=False),
        sa.Column("effect_direction", sa.String(), nullable=False),
        sa.Column("effect_provenance", sa.String(), nullable=False),
        sa.Column("significance_type", sa.String(), nullable=False),
        sa.Column("significance_value", sa.Float(), nullable=False),
        sa.Column("significance_provenance", sa.String(), nullable=False),
        sa.Column("reliability_rating", sa.String(), nullable=False),
        sa.Column("reliability_provenance", sa.String(), nullable=False),
        sa.Column("visibility", sa.String(), nullable=False),
    )

    op.create_table(
        "techniques",
        sa.Column("technique_id", sa.String(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(), nullable=False),
        sa.Column("mapping_json", sa.JSON()),
    )


def downgrade() -> None:
    op.drop_table("techniques")
    op.drop_table("results")
    op.drop_table("outcomes")
    op.drop_table("studies")
