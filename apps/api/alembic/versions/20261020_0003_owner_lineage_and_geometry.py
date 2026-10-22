"""Add owner resolution, raw lineage, and PostGIS point support.

Revision ID: 20261020_0003
Revises: 20261020_0002
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "20261020_0003"
down_revision: str | None = "20261020_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.add_column("source_records", sa.Column("raw_file_path", sa.Text(), nullable=True))
    op.add_column("source_records", sa.Column("sync_run_id", uuid_type, nullable=True))
    op.create_foreign_key("fk_source_records_sync_run", "source_records", "sync_runs", ["sync_run_id"], ["id"])
    for table in ("properties", "addresses", "owners", "property_ownership", "assessments", "sales"):
        op.add_column(table, sa.Column("source_record_id", uuid_type, nullable=True))
        op.create_foreign_key(f"fk_{table}_source_record", table, "source_records", ["source_record_id"], ["id"])
    op.add_column(
        "addresses", sa.Column("location", Geometry("POINT", srid=4326, spatial_index=False), nullable=True)
    )
    op.create_index("ix_addresses_location", "addresses", ["location"], postgresql_using="gist")
    op.add_column("owners", sa.Column("entity_type", sa.String(40), nullable=True))
    op.add_column("owners", sa.Column("raw_mailing_address", sa.Text(), nullable=True))
    op.add_column("owners", sa.Column("normalized_mailing_address", sa.Text(), nullable=True))
    op.add_column("owners", sa.Column("mailing_postal_code", sa.String(10), nullable=True))
    op.add_column("owners", sa.Column("resolution_status", sa.String(30), server_default="unresolved", nullable=False))
    op.add_column("owners", sa.Column("resolution_confidence", sa.Float(), nullable=True))
    op.create_index("ix_owners_name_mailing", "owners", ["normalized_name", "normalized_mailing_address"])
    op.add_column("property_ownership", sa.Column("ownership_percentage", sa.Numeric(5, 2), nullable=True))
    op.add_column("property_ownership", sa.Column("match_method", sa.String(50), nullable=True))
    op.add_column("property_ownership", sa.Column("match_confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    for column in ("match_confidence", "match_method", "ownership_percentage"):
        op.drop_column("property_ownership", column)
    op.drop_index("ix_owners_name_mailing", table_name="owners")
    for column in ("resolution_confidence", "resolution_status", "mailing_postal_code", "normalized_mailing_address", "raw_mailing_address", "entity_type"):
        op.drop_column("owners", column)
    op.drop_index("ix_addresses_location", table_name="addresses", postgresql_using="gist")
    op.drop_column("addresses", "location")
    for table in ("sales", "assessments", "property_ownership", "owners", "addresses", "properties"):
        op.drop_constraint(f"fk_{table}_source_record", table, type_="foreignkey")
        op.drop_column(table, "source_record_id")
    op.drop_constraint("fk_source_records_sync_run", "source_records", type_="foreignkey")
    op.drop_column("source_records", "sync_run_id")
    op.drop_column("source_records", "raw_file_path")
