from decimal import Decimal

from sqlalchemy import Numeric, UniqueConstraint

from app.db.base import Base
from app.models import Assessment, ExternalIdentifier, Property, Sale, SourceRecord


def test_foundational_tables_are_registered() -> None:
    assert {
        "addresses",
        "assessments",
        "owners",
        "properties",
        "property_ownership",
        "property_source_ids",
        "sales",
        "source_records",
        "sync_runs",
    } <= set(Base.metadata.tables)


def test_imported_entities_require_provenance() -> None:
    for model in (Property, Assessment, Sale):
        for name in ("source", "source_identifier", "observed_at"):
            assert model.__table__.c[name].nullable is False


def test_money_columns_are_fixed_precision() -> None:
    for column in (Assessment.assessed_value, Sale.sale_price):
        assert isinstance(column.type, Numeric)
        assert column.type.precision == 14
        assert column.type.scale == 2
    assert Decimal("0.10") + Decimal("0.20") == Decimal("0.30")


def test_source_identity_constraints_prevent_duplicates() -> None:
    external_constraints = {
        constraint.name
        for constraint in ExternalIdentifier.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    raw_constraints = {
        constraint.name
        for constraint in SourceRecord.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert "uq_property_source_identifier" in external_constraints
    assert "uq_source_record_hash" in raw_constraints
    for model, expected in (
        (Assessment, "uq_assessment_source_identifier"),
        (Sale, "uq_sale_source_identifier"),
    ):
        names = {
            constraint.name
            for constraint in model.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert expected in names
