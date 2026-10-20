"""Create the foundational property intelligence schema.

Revision ID: 20261020_0001
Revises:
Create Date: 2026-10-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261020_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def provenance() -> list[sa.Column]:
    return [
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_identifier", sa.String(length=200), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)

    op.create_table(
        "addresses",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("raw_address", sa.Text(), nullable=True),
        sa.Column("normalized_address", sa.Text(), nullable=True),
        sa.Column("street_number", sa.String(length=30), nullable=True),
        sa.Column("street_name", sa.String(length=120), nullable=True),
        sa.Column("street_suffix", sa.String(length=20), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("postal_code", sa.String(length=10), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        *timestamps(),
        *provenance(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_addresses_normalized_address", "addresses", ["normalized_address"])

    op.create_table(
        "owners",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("raw_name", sa.Text(), nullable=True),
        sa.Column("normalized_name", sa.Text(), nullable=True),
        sa.Column("mailing_city", sa.String(length=120), nullable=True),
        sa.Column("mailing_state", sa.String(length=2), nullable=True),
        sa.Column("is_absentee", sa.Boolean(), nullable=True),
        sa.Column("portfolio_count", sa.Integer(), nullable=True),
        *timestamps(),
        *provenance(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_owners_normalized_name", "owners", ["normalized_name"])

    op.create_table(
        "source_records",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_identifier", sa.String(length=200), nullable=False),
        sa.Column("record_hash", sa.String(length=128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "record_hash", name="uq_source_record_hash"),
    )
    op.create_index("ix_source_records_lookup", "source_records", ["source", "source_identifier"])

    op.create_table(
        "sync_runs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("records_seen", sa.Integer(), nullable=False),
        sa.Column("records_created", sa.Integer(), nullable=False),
        sa.Column("records_updated", sa.Integer(), nullable=False),
        sa.Column("records_failed", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "properties",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("county", sa.String(length=100), nullable=True),
        sa.Column("property_type", sa.String(length=50), nullable=True),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("bedrooms", sa.Integer(), nullable=True),
        sa.Column("bathrooms", sa.Float(), nullable=True),
        sa.Column("square_feet", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("address_id", uuid_type, nullable=True),
        *timestamps(),
        *provenance(),
        sa.ForeignKeyConstraint(["address_id"], ["addresses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_properties_county", "properties", ["state", "county"])

    op.create_table(
        "property_ownership",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("property_id", uuid_type, nullable=False),
        sa.Column("owner_id", uuid_type, nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acquired_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *timestamps(),
        *provenance(),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_property_ownership_current", "property_ownership", ["property_id", "is_current"])

    op.create_table(
        "assessments",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("property_id", uuid_type, nullable=False),
        sa.Column("assessment_year", sa.Integer(), nullable=True),
        sa.Column("assessed_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        *timestamps(),
        *provenance(),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sales",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("property_id", uuid_type, nullable=False),
        sa.Column("sale_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sale_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("deed_type", sa.String(length=50), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        *timestamps(),
        *provenance(),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "property_source_ids",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("property_id", uuid_type, nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_identifier", sa.String(length=200), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_identifier", name="uq_property_source_identifier"),
    )


def downgrade() -> None:
    op.drop_table("property_source_ids")
    op.drop_table("sales")
    op.drop_table("assessments")
    op.drop_index("ix_property_ownership_current", table_name="property_ownership")
    op.drop_table("property_ownership")
    op.drop_index("ix_properties_county", table_name="properties")
    op.drop_table("properties")
    op.drop_table("sync_runs")
    op.drop_index("ix_source_records_lookup", table_name="source_records")
    op.drop_table("source_records")
    op.drop_index("ix_owners_normalized_name", table_name="owners")
    op.drop_table("owners")
    op.drop_index("ix_addresses_normalized_address", table_name="addresses")
    op.drop_table("addresses")
