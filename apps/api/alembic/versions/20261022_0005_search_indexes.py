"""Add property-browser query indexes.

Revision ID: 20261022_0005
Revises: 20261021_0004
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261022_0005"
down_revision: str | None = "20261021_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_properties_county_type", "properties", ["county", "property_type"])
    op.create_index("ix_addresses_postal_code", "addresses", ["postal_code"])
    op.create_index("ix_assessments_property_year", "assessments", ["property_id", "assessment_year"])
    op.create_index("ix_sales_property_date", "sales", ["property_id", "sale_date"])
    op.create_index("ix_property_source_ids_property", "property_source_ids", ["property_id"])


def downgrade() -> None:
    op.drop_index("ix_property_source_ids_property", table_name="property_source_ids")
    op.drop_index("ix_sales_property_date", table_name="sales")
    op.drop_index("ix_assessments_property_year", table_name="assessments")
    op.drop_index("ix_addresses_postal_code", table_name="addresses")
    op.drop_index("ix_properties_county_type", table_name="properties")
