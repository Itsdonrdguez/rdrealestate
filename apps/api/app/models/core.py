from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ProvenanceMixin:
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    source_identifier: Mapped[str] = mapped_column(String(200), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Property(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "properties"
    __table_args__ = (Index("ix_properties_county", "state", "county"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state: Mapped[str] = mapped_column(String(2), nullable=False, default="MD")
    county: Mapped[str | None] = mapped_column(String(100), nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    year_built: Mapped[int | None] = mapped_column(nullable=True)
    bedrooms: Mapped[int | None] = mapped_column(nullable=True)
    bathrooms: Mapped[float | None] = mapped_column(Float, nullable=True)
    square_feet: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    address_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("addresses.id"), nullable=True)
    address: Mapped["Address | None"] = relationship(back_populates="properties")
    ownerships: Mapped[list["PropertyOwnership"]] = relationship(back_populates="property")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="property")
    sales: Mapped[list["Sale"]] = relationship(back_populates="property")
    external_identifiers: Mapped[list["ExternalIdentifier"]] = relationship(back_populates="property")


class Address(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "addresses"
    __table_args__ = (Index("ix_addresses_normalized_address", "normalized_address"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    street_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    street_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    street_suffix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    properties: Mapped[list[Property]] = relationship(back_populates="address")


class Owner(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "owners"
    __table_args__ = (Index("ix_owners_normalized_name", "normalized_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    mailing_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mailing_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    is_absentee: Mapped[bool | None] = mapped_column(nullable=True)
    portfolio_count: Mapped[int | None] = mapped_column(nullable=True)

    ownerships: Mapped[list["PropertyOwnership"]] = relationship(back_populates="owner")


class PropertyOwnership(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "property_ownership"
    __table_args__ = (Index("ix_property_ownership_current", "property_id", "is_current"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id"), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("owners.id"), nullable=False)
    acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acquired_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    property: Mapped[Property] = relationship(back_populates="ownerships")
    owner: Mapped[Owner] = relationship(back_populates="ownerships")


class Assessment(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "assessments"
    __table_args__ = (UniqueConstraint("source", "source_identifier", name="uq_assessment_source_identifier"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id"), nullable=False)
    assessment_year: Mapped[int | None] = mapped_column(nullable=True)
    assessed_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    property: Mapped[Property] = relationship(back_populates="assessments")


class Sale(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "sales"
    __table_args__ = (UniqueConstraint("source", "source_identifier", name="uq_sale_source_identifier"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id"), nullable=False)
    sale_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    deed_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    property: Mapped[Property] = relationship(back_populates="sales")


class ExternalIdentifier(Base, TimestampMixin):
    __tablename__ = "property_source_ids"
    __table_args__ = (UniqueConstraint("source", "source_identifier", name="uq_property_source_identifier"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    source_identifier: Mapped[str] = mapped_column(String(200), nullable=False)

    property: Mapped[Property] = relationship(back_populates="external_identifiers")


class SourceRecord(Base, TimestampMixin):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint("source", "record_hash", name="uq_source_record_hash"),
        Index("ix_source_records_lookup", "source", "source_identifier"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    source_identifier: Mapped[str] = mapped_column(String(200), nullable=False)
    record_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)


class SyncRun(Base, TimestampMixin):
    __tablename__ = "sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    records_seen: Mapped[int] = mapped_column(default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
