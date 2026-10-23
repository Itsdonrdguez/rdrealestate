"""Add persistent ingestion benchmark metrics.

Revision ID: 20261021_0004
Revises: 20261020_0003
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261021_0004"
down_revision: str | None = "20261020_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for name in (
        "records_validated", "records_skipped", "pages_fetched", "api_retries",
        "rate_limits", "server_errors", "raw_bytes", "checkpoint_count",
    ):
        op.add_column("sync_runs", sa.Column(name, sa.Integer(), server_default="0", nullable=False))
    op.add_column("sync_runs", sa.Column("elapsed_seconds", sa.Float(), nullable=True))
    op.add_column("sync_runs", sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("sync_runs", "metrics")
    op.drop_column("sync_runs", "elapsed_seconds")
    for name in reversed((
        "records_validated", "records_skipped", "pages_fetched", "api_retries",
        "rate_limits", "server_errors", "raw_bytes", "checkpoint_count",
    )):
        op.drop_column("sync_runs", name)
