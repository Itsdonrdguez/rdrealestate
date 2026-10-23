from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, select, text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Address, Assessment, ExternalIdentifier, Property, Sale, SyncRun

router = APIRouter(prefix="/api", tags=["intelligence"])


def _latest_fact(model: type[Assessment] | type[Sale], date_column, value_column, label: str):
    ranked = select(
        model.property_id.label("property_id"),
        date_column.label(f"{label}_date"),
        value_column.label(f"{label}_value"),
        func.row_number().over(
            partition_by=model.property_id,
            order_by=(date_column.desc().nullslast(), model.observed_at.desc()),
        ).label("rank"),
    ).subquery()
    return select(ranked).where(ranked.c.rank == 1).subquery()


LATEST_ASSESSMENT = _latest_fact(Assessment, Assessment.assessment_year, Assessment.assessed_value, "assessment")
LATEST_SALE = _latest_fact(Sale, Sale.sale_date, Sale.sale_price, "sale")


def _property_filters(
    statement: Select,
    *,
    county: str | None,
    postal_code: str | None,
    property_type: str | None,
    query: str | None,
    min_assessed_value: int | None,
    max_assessed_value: int | None,
    include_assessment_filters: bool = True,
) -> Select:
    if county:
        statement = statement.where(func.lower(Property.county) == county.lower())
    if postal_code:
        statement = statement.where(Address.postal_code == postal_code)
    if property_type:
        statement = statement.where(Property.property_type == property_type)
    if query:
        statement = statement.where(Address.normalized_address.ilike(f"%{query.strip()}%"))
    if include_assessment_filters and min_assessed_value is not None:
        statement = statement.where(LATEST_ASSESSMENT.c.assessment_value >= min_assessed_value)
    if include_assessment_filters and max_assessed_value is not None:
        statement = statement.where(LATEST_ASSESSMENT.c.assessment_value <= max_assessed_value)
    return statement


@router.get("/properties")
def list_properties(
    county: str | None = Query("Charles", max_length=100),
    postal_code: str | None = Query(None, max_length=10),
    property_type: str | None = Query(None, max_length=100),
    query: str | None = Query(None, max_length=150),
    min_assessed_value: int | None = Query(None, ge=0),
    max_assessed_value: int | None = Query(None, ge=0),
    sort: Literal["address", "assessed_value", "sale_date", "year_built"] = "address",
    direction: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    base = select(Property.id).join(Address, Property.address_id == Address.id)
    base = _property_filters(
        base,
        county=county,
        postal_code=postal_code,
        property_type=property_type,
        query=query,
        min_assessed_value=min_assessed_value,
        max_assessed_value=max_assessed_value,
        include_assessment_filters=False,
    )
    assessment_exists = select(Assessment.id).where(Assessment.property_id == Property.id)
    if min_assessed_value is not None:
        assessment_exists = assessment_exists.where(Assessment.assessed_value >= min_assessed_value)
    if max_assessed_value is not None:
        assessment_exists = assessment_exists.where(Assessment.assessed_value <= max_assessed_value)
    if min_assessed_value is not None or max_assessed_value is not None:
        base = base.where(assessment_exists.exists())
    total = int(db.scalar(select(func.count()).select_from(base.subquery())) or 0)

    statement = (
        select(
            Property.id,
            Property.county,
            Property.property_type,
            Property.year_built,
            Property.square_feet,
            Address.normalized_address,
            Address.city,
            Address.postal_code,
            Address.latitude,
            Address.longitude,
            ExternalIdentifier.source_identifier.label("account_id"),
            LATEST_ASSESSMENT.c.assessment_date,
            LATEST_ASSESSMENT.c.assessment_value,
            LATEST_SALE.c.sale_date,
            LATEST_SALE.c.sale_value,
        )
        .join(Address, Property.address_id == Address.id)
        .outerjoin(LATEST_ASSESSMENT, LATEST_ASSESSMENT.c.property_id == Property.id)
        .outerjoin(LATEST_SALE, LATEST_SALE.c.property_id == Property.id)
        .outerjoin(ExternalIdentifier, ExternalIdentifier.property_id == Property.id)
    )
    statement = _property_filters(
        statement,
        county=county,
        postal_code=postal_code,
        property_type=property_type,
        query=query,
        min_assessed_value=min_assessed_value,
        max_assessed_value=max_assessed_value,
    )
    sort_columns = {
        "address": Address.normalized_address,
        "assessed_value": LATEST_ASSESSMENT.c.assessment_value,
        "sale_date": LATEST_SALE.c.sale_date,
        "year_built": Property.year_built,
    }
    sort_column = sort_columns[sort]
    ordering = sort_column.desc().nullslast() if direction == "desc" else sort_column.asc().nullslast()
    statement = statement.order_by(ordering, Property.id).offset((page - 1) * page_size).limit(page_size)
    items = [dict(row._mapping) for row in db.execute(statement)]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}


@router.get("/properties/facets")
def property_facets(county: str = Query("Charles", max_length=100), db: Session = Depends(get_db)) -> dict[str, object]:
    zip_rows = db.execute(
        select(Address.postal_code, func.count(Property.id))
        .join(Property, Property.address_id == Address.id)
        .where(func.lower(Property.county) == county.lower(), Address.postal_code.is_not(None))
        .group_by(Address.postal_code)
        .order_by(Address.postal_code)
    )
    type_rows = db.execute(
        select(Property.property_type, func.count(Property.id))
        .where(func.lower(Property.county) == county.lower(), Property.property_type.is_not(None))
        .group_by(Property.property_type)
        .order_by(func.count(Property.id).desc())
        .limit(40)
    )
    return {
        "postal_codes": [{"value": value, "count": count} for value, count in zip_rows],
        "property_types": [{"value": value, "count": count} for value, count in type_rows],
    }


def _directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


@router.get("/system/health")
def system_health(db: Session = Depends(get_db)) -> dict[str, object]:
    latest = db.scalar(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(1))
    database_bytes = int(db.scalar(text("SELECT pg_database_size(current_database())")) or 0)
    data_root = Path(os.getenv("DATA_ROOT", "data"))
    raw_bytes = _directory_size(data_root / "raw")
    preflight_path = data_root / "exports" / "charles-preflight.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8")) if preflight_path.exists() else None
    capacity = None
    if latest and preflight and latest.records_seen:
        statewide_records = int(preflight["statewide_records"])
        database_growth = max(0, database_bytes - int(preflight["database_bytes"]))
        projected_raw = latest.raw_bytes / latest.records_seen * statewide_records
        projected_database = database_growth / latest.records_seen * statewide_records
        required_bytes = int(2 * (projected_raw + projected_database))
        capacity = {
            "host_free_bytes": int(preflight["host_free_bytes"]),
            "projected_raw_bytes": int(projected_raw),
            "projected_database_bytes": int(projected_database),
            "required_bytes_at_2x": required_bytes,
            "statewide_go": int(preflight["host_free_bytes"]) >= required_bytes,
        }
    run = None
    if latest:
        run = {
            "id": str(latest.id),
            "source": latest.source,
            "status": latest.status,
            "started_at": latest.started_at,
            "finished_at": latest.finished_at,
            "records_seen": latest.records_seen,
            "records_created": latest.records_created,
            "records_updated": latest.records_updated,
            "records_failed": latest.records_failed,
            "records_validated": latest.records_validated,
            "pages_fetched": latest.pages_fetched,
            "api_retries": latest.api_retries,
            "raw_bytes": latest.raw_bytes,
            "elapsed_seconds": latest.elapsed_seconds,
        }
    return {"status": "ok", "database_bytes": database_bytes, "raw_directory_bytes": raw_bytes, "latest_sync": run, "capacity_preflight": preflight, "capacity": capacity}
