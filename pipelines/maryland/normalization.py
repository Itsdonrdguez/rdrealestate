from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from . import fields


@dataclass(frozen=True)
class MarylandPropertyRecord:
    source_identifier: str
    observed_at: datetime
    county: str
    raw_address: str | None
    normalized_address: str | None
    street_number: str | None
    street_name: str | None
    street_suffix: str | None
    unit: str | None
    city: str | None
    postal_code: str | None
    latitude: float | None
    longitude: float | None
    property_type: str | None
    land_use: str | None
    year_built: int | None
    square_feet: int | None
    assessed_value: Decimal | None
    assessment_year: int | None
    sale_date: datetime | None
    sale_price: Decimal | None
    owner_occupied: bool | None


def clean_text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned or None


def normalize_address(*parts: object) -> str | None:
    cleaned = [clean_text(part) for part in parts]
    return " ".join(part.upper() for part in cleaned if part) or None


def parse_int(value: object) -> int | None:
    text = clean_text(value)
    if not text or text in {"0", "0000"}:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_decimal(value: object) -> Decimal | None:
    text = clean_text(value)
    if not text:
        return None
    try:
        return Decimal(text.replace(",", ""))
    except InvalidOperation:
        return None


def parse_float(value: object) -> float | None:
    text = clean_text(value)
    try:
        return float(text) if text else None
    except ValueError:
        return None


def parse_date(value: object, *formats: str) -> datetime | None:
    text = clean_text(value)
    if not text or text.startswith("0000"):
        return None
    for date_format in formats:
        try:
            return datetime.strptime(text, date_format).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def normalize_record(record: dict[str, object]) -> MarylandPropertyRecord:
    owner_code = clean_text(record.get(fields.OWNER_OCCUPANCY))
    return MarylandPropertyRecord(
        source_identifier=str(record[fields.ACCOUNT_ID]),
        observed_at=parse_date(record.get(fields.LAST_UPDATED), "%Y%m%d") or datetime.now(UTC),
        county=clean_text(record.get(fields.COUNTY)) or "Unknown",
        raw_address=clean_text(record.get(fields.ADDRESS)),
        normalized_address=normalize_address(
            record.get(fields.ADDRESS), record.get(fields.CITY), "MD", record.get(fields.ZIP_CODE)
        ),
        street_number=clean_text(record.get(fields.STREET_NUMBER)),
        street_name=clean_text(record.get(fields.STREET_NAME)),
        street_suffix=clean_text(record.get(fields.STREET_TYPE)),
        unit=clean_text(record.get(fields.UNIT)),
        city=clean_text(record.get(fields.CITY)),
        postal_code=clean_text(record.get(fields.ZIP_CODE)),
        latitude=parse_float(record.get(fields.LATITUDE)),
        longitude=parse_float(record.get(fields.LONGITUDE)),
        property_type=clean_text(record.get(fields.PROPERTY_TYPE)),
        land_use=clean_text(record.get(fields.LAND_USE)),
        year_built=parse_int(record.get(fields.YEAR_BUILT)),
        square_feet=parse_int(record.get(fields.SQUARE_FEET)),
        assessed_value=parse_decimal(record.get(fields.ASSESSED_VALUE)),
        assessment_year=parse_int(record.get(fields.ASSESSMENT_YEAR)),
        sale_date=parse_date(record.get(fields.SALE_DATE), "%Y.%m.%d"),
        sale_price=parse_decimal(record.get(fields.SALE_PRICE)),
        owner_occupied=True if owner_code == "H" else False if owner_code else None,
    )
