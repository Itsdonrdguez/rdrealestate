"""Add source identity constraints to historical facts.

Revision ID: 20261020_0002
Revises: 20261020_0001
Create Date: 2026-10-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261020_0002"
down_revision: str | None = "20261020_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_assessment_source_identifier", "assessments", ["source", "source_identifier"]
    )
    op.create_unique_constraint("uq_sale_source_identifier", "sales", ["source", "source_identifier"])


def downgrade() -> None:
    op.drop_constraint("uq_sale_source_identifier", "sales", type_="unique")
    op.drop_constraint("uq_assessment_source_identifier", "assessments", type_="unique")
