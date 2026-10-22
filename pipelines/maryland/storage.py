from __future__ import annotations

import hashlib
import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from app.models import Address, Assessment, ExternalIdentifier, Property, Sale, SourceRecord

from .fields import SOURCE
from .normalization import MarylandPropertyRecord


def canonical_payload(record: dict[str, object]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def store_record(
    session: Session,
    raw: dict[str, object],
    normalized: MarylandPropertyRecord,
    *,
    sync_run_id: uuid.UUID,
    raw_file_path: str,
) -> tuple[Property, bool]:
    """Persist one validated record. Returns the property and whether it was created."""
    payload = canonical_payload(raw)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    source_record = session.scalar(
        select(SourceRecord).where(SourceRecord.source == SOURCE, SourceRecord.record_hash == digest)
    )
    if not source_record:
        source_record = SourceRecord(
                source=SOURCE,
                source_identifier=normalized.source_identifier,
                record_hash=digest,
                observed_at=normalized.observed_at,
                raw_payload=payload,
                raw_file_path=raw_file_path,
                sync_run_id=sync_run_id,
            )
        session.add(source_record)
        session.flush()
    elif not source_record.raw_file_path:
        source_record.raw_file_path = raw_file_path
        source_record.sync_run_id = sync_run_id

    external_id = session.scalar(
        select(ExternalIdentifier).where(
            ExternalIdentifier.source == SOURCE,
            ExternalIdentifier.source_identifier == normalized.source_identifier,
        )
    )
    created = external_id is None
    if created:
        address = Address(
            source=SOURCE,
            source_identifier=normalized.source_identifier,
            observed_at=normalized.observed_at,
            source_record_id=source_record.id,
            raw_address=normalized.raw_address,
            normalized_address=normalized.normalized_address,
            street_number=normalized.street_number,
            street_name=normalized.street_name,
            street_suffix=normalized.street_suffix,
            unit=normalized.unit,
            city=normalized.city,
            state="MD",
            postal_code=normalized.postal_code,
            latitude=normalized.latitude,
            longitude=normalized.longitude,
            location=(
                WKTElement(f"POINT({normalized.longitude} {normalized.latitude})", srid=4326)
                if normalized.longitude is not None and normalized.latitude is not None
                else None
            ),
        )
        property_record = Property(
            source=SOURCE,
            source_identifier=normalized.source_identifier,
            observed_at=normalized.observed_at,
            source_record_id=source_record.id,
            state="MD",
            county=normalized.county,
            property_type=normalized.property_type or normalized.land_use,
            year_built=normalized.year_built,
            square_feet=normalized.square_feet,
            address=address,
        )
        session.add(property_record)
        session.flush()
        session.add(
            ExternalIdentifier(
                property_id=property_record.id,
                source=SOURCE,
                source_identifier=normalized.source_identifier,
            )
        )
    else:
        property_record = external_id.property
        property_record.observed_at = normalized.observed_at
        property_record.source_record_id = source_record.id
        property_record.county = normalized.county
        property_record.property_type = normalized.property_type or normalized.land_use
        property_record.year_built = normalized.year_built
        property_record.square_feet = normalized.square_feet
        if property_record.address:
            property_record.address.observed_at = normalized.observed_at
            property_record.address.source_record_id = source_record.id
            property_record.address.raw_address = normalized.raw_address
            property_record.address.normalized_address = normalized.normalized_address
            property_record.address.latitude = normalized.latitude
            property_record.address.longitude = normalized.longitude
            property_record.address.location = (
                WKTElement(f"POINT({normalized.longitude} {normalized.latitude})", srid=4326)
                if normalized.longitude is not None and normalized.latitude is not None
                else None
            )

    assessment_identifier = (
        f"{normalized.source_identifier}:assessment:{normalized.assessment_year or 'unknown'}:"
        f"{normalized.assessed_value or 'unknown'}"
    )
    if normalized.assessed_value is not None and not session.scalar(
        select(Assessment).where(
            Assessment.source == SOURCE, Assessment.source_identifier == assessment_identifier
        )
    ):
        session.add(
            Assessment(
                property=property_record,
                source=SOURCE,
                source_identifier=assessment_identifier,
                observed_at=normalized.observed_at,
                source_record_id=source_record.id,
                assessment_year=normalized.assessment_year,
                assessed_value=normalized.assessed_value,
            )
        )

    sale_identifier = (
        f"{normalized.source_identifier}:sale:"
        f"{normalized.sale_date.date().isoformat() if normalized.sale_date else 'unknown'}:"
        f"{normalized.sale_price or 'unknown'}"
    )
    if normalized.sale_date and normalized.sale_price and normalized.sale_price > 0 and not session.scalar(
        select(Sale).where(Sale.source == SOURCE, Sale.source_identifier == sale_identifier)
    ):
        session.add(
            Sale(
                property=property_record,
                source=SOURCE,
                source_identifier=sale_identifier,
                observed_at=normalized.observed_at,
                source_record_id=source_record.id,
                sale_date=normalized.sale_date,
                sale_price=normalized.sale_price,
            )
        )
    return property_record, created
