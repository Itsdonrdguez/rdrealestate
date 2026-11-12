from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from app.models import Address, Assessment, ExternalIdentifier, Property, Sale, SourceRecord

from .fields import SOURCE
from .normalization import MarylandPropertyRecord


@dataclass(frozen=True)
class StorageRecord:
    raw: dict[str, object]
    normalized: MarylandPropertyRecord
    raw_file_path: str


@dataclass(frozen=True)
class StorageResult:
    created: int
    updated: int


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
    """Persist one record through the page-oriented implementation."""
    result, properties = store_records(
        session,
        [StorageRecord(raw=raw, normalized=normalized, raw_file_path=raw_file_path)],
        sync_run_id=sync_run_id,
    )
    return properties[0], result.created == 1


def store_records(
    session: Session,
    records: Sequence[StorageRecord],
    *,
    sync_run_id: uuid.UUID,
) -> tuple[StorageResult, list[Property]]:
    """Persist a source page with a bounded number of database round trips."""
    if not records:
        return StorageResult(created=0, updated=0), []

    prepared = []
    for item in records:
        payload = canonical_payload(item.raw)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assessment_identifier = (
            f"{item.normalized.source_identifier}:assessment:"
            f"{item.normalized.assessment_year or 'unknown'}:"
            f"{item.normalized.assessed_value or 'unknown'}"
        )
        sale_identifier = (
            f"{item.normalized.source_identifier}:sale:"
            f"{item.normalized.sale_date.date().isoformat() if item.normalized.sale_date else 'unknown'}:"
            f"{item.normalized.sale_price or 'unknown'}"
        )
        prepared.append((item, payload, digest, assessment_identifier, sale_identifier))

    digests = [row[2] for row in prepared]
    source_records = {
        row.record_hash: row
        for row in session.scalars(
            select(SourceRecord).where(SourceRecord.source == SOURCE, SourceRecord.record_hash.in_(digests))
        )
    }
    new_source_records: list[SourceRecord] = []
    for item, payload, digest, _, _ in prepared:
        source_record = source_records.get(digest)
        if source_record is None:
            source_record = SourceRecord(
                id=uuid.uuid4(),
                source=SOURCE,
                source_identifier=item.normalized.source_identifier,
                record_hash=digest,
                observed_at=item.normalized.observed_at,
                raw_payload=payload,
                raw_file_path=item.raw_file_path,
                sync_run_id=sync_run_id,
            )
            source_records[digest] = source_record
            new_source_records.append(source_record)
        elif not source_record.raw_file_path:
            source_record.raw_file_path = item.raw_file_path
            source_record.sync_run_id = sync_run_id
    if new_source_records:
        session.add_all(new_source_records)
        # Provenance rows must exist before the page's dependent facts are
        # emitted. This remains one batched flush rather than one per record.
        session.flush(new_source_records)

    identifiers = [item.normalized.source_identifier for item in records]
    existing_properties = {
        external.source_identifier: (external, property_record, address)
        for external, property_record, address in session.execute(
            select(ExternalIdentifier, Property, Address)
            .join(Property, ExternalIdentifier.property_id == Property.id)
            .outerjoin(Address, Property.address_id == Address.id)
            .where(
                ExternalIdentifier.source == SOURCE,
                ExternalIdentifier.source_identifier.in_(identifiers),
            )
        )
    }
    assessment_identifiers = [row[3] for row in prepared if row[0].normalized.assessed_value is not None]
    sale_identifiers = [
        row[4]
        for row in prepared
        if row[0].normalized.sale_date
        and row[0].normalized.sale_price
        and row[0].normalized.sale_price > 0
    ]
    existing_assessments = set(
        session.scalars(
            select(Assessment.source_identifier).where(
                Assessment.source == SOURCE,
                Assessment.source_identifier.in_(assessment_identifiers),
            )
        )
    ) if assessment_identifiers else set()
    existing_sales = set(
        session.scalars(
            select(Sale.source_identifier).where(
                Sale.source == SOURCE,
                Sale.source_identifier.in_(sale_identifiers),
            )
        )
    ) if sale_identifiers else set()

    created = updated = 0
    properties: list[Property] = []
    for item, payload, digest, assessment_identifier, sale_identifier in prepared:
        normalized = item.normalized
        source_record = source_records[digest]

        existing = existing_properties.get(normalized.source_identifier)
        location = (
            WKTElement(f"POINT({normalized.longitude} {normalized.latitude})", srid=4326)
            if normalized.longitude is not None and normalized.latitude is not None
            else None
        )
        if existing is None:
            address = Address(
                id=uuid.uuid4(),
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
                location=location,
            )
            property_record = Property(
                id=uuid.uuid4(),
                source=SOURCE,
                source_identifier=normalized.source_identifier,
                observed_at=normalized.observed_at,
                source_record_id=source_record.id,
                state="MD",
                county=normalized.county,
                property_type=normalized.property_type or normalized.land_use,
                year_built=normalized.year_built,
                square_feet=normalized.square_feet,
                address_id=address.id,
            )
            session.add_all(
                [
                    address,
                    property_record,
                    ExternalIdentifier(
                        id=uuid.uuid4(),
                        property_id=property_record.id,
                        source=SOURCE,
                        source_identifier=normalized.source_identifier,
                    ),
                ]
            )
            created += 1
        else:
            _, property_record, address = existing
            property_record.observed_at = normalized.observed_at
            property_record.source_record_id = source_record.id
            property_record.county = normalized.county
            property_record.property_type = normalized.property_type or normalized.land_use
            property_record.year_built = normalized.year_built
            property_record.square_feet = normalized.square_feet
            if address:
                address.observed_at = normalized.observed_at
                address.source_record_id = source_record.id
                address.raw_address = normalized.raw_address
                address.normalized_address = normalized.normalized_address
                address.street_number = normalized.street_number
                address.street_name = normalized.street_name
                address.street_suffix = normalized.street_suffix
                address.unit = normalized.unit
                address.city = normalized.city
                address.postal_code = normalized.postal_code
                address.latitude = normalized.latitude
                address.longitude = normalized.longitude
                address.location = location
            updated += 1

        if normalized.assessed_value is not None and assessment_identifier not in existing_assessments:
            session.add(
                Assessment(
                    id=uuid.uuid4(),
                    property_id=property_record.id,
                    source=SOURCE,
                    source_identifier=assessment_identifier,
                    observed_at=normalized.observed_at,
                    source_record_id=source_record.id,
                    assessment_year=normalized.assessment_year,
                    assessed_value=normalized.assessed_value,
                )
            )
            existing_assessments.add(assessment_identifier)

        if (
            normalized.sale_date
            and normalized.sale_price
            and normalized.sale_price > 0
            and sale_identifier not in existing_sales
        ):
            session.add(
                Sale(
                    id=uuid.uuid4(),
                    property_id=property_record.id,
                    source=SOURCE,
                    source_identifier=sale_identifier,
                    observed_at=normalized.observed_at,
                    source_record_id=source_record.id,
                    sale_date=normalized.sale_date,
                    sale_price=normalized.sale_price,
                )
            )
            existing_sales.add(sale_identifier)
        properties.append(property_record)

    return StorageResult(created=created, updated=updated), properties
