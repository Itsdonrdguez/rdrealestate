from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.models import SyncRun

from .connector import ConnectorStats, MarylandSdatConnector
from .fields import API_URL, SOURCE
from .normalization import normalize_record
from .raw_store import RawStore
from .storage import store_record
from .validation import RecordValidationError, validate_page_schema, validate_record

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    seen: int
    created: int
    updated: int
    failed: int
    raw_directory: Path
    metrics: dict[str, object]


def run_pipeline(
    session_factory: sessionmaker[Session] | None,
    *,
    raw_root: Path,
    app_token: str | None = None,
    limit: int | None = None,
    where: str | None = None,
    dry_run: bool = False,
    client=None,
    resume_run_id: str | None = None,
    min_free_bytes: int = 2_000_000_000,
    max_pages: int | None = None,
    county: str | None = None,
) -> PipelineResult:
    started = time.monotonic()
    run_uuid = uuid.UUID(resume_run_id) if resume_run_id else uuid.uuid4()
    run_id = str(run_uuid)
    raw_store = RawStore(raw_root, run_id, resume=bool(resume_run_id), min_free_bytes=min_free_bytes)
    seen = created = updated = failed = 0
    validated_count = skipped = checkpoint_count = 0
    prior_elapsed = 0.0
    prior_pages = prior_retries = prior_rate_limits = prior_server_errors = 0
    cursor: str | None = None
    next_page = 1
    if resume_run_id:
        checkpoint = raw_store.read_checkpoint()
        cursor = str(checkpoint["cursor"]) if checkpoint.get("cursor") else None
        next_page = int(checkpoint["next_page"])
        seen = int(checkpoint["seen"])
        created = int(checkpoint["created"])
        updated = int(checkpoint["updated"])
        failed = int(checkpoint["failed"])
        validated_count = int(checkpoint.get("validated", 0))
        skipped = int(checkpoint.get("skipped", 0))
        checkpoint_count = int(checkpoint.get("checkpoint_count", 0))
        prior_elapsed = float(checkpoint.get("elapsed_seconds", 0.0))
    error_message: str | None = None

    sync_run: SyncRun | None = None
    connector_stats = ConnectorStats()
    if not dry_run:
        if session_factory is None:
            raise ValueError("session_factory is required unless dry_run is enabled")
        with session_factory.begin() as session:
            sync_run = session.get(SyncRun, run_uuid)
            if sync_run:
                prior_pages = sync_run.pages_fetched
                prior_retries = sync_run.api_retries
                prior_rate_limits = sync_run.rate_limits
                prior_server_errors = sync_run.server_errors
                sync_run.status = "running"
                sync_run.error = None
                sync_run.finished_at = None
            else:
                sync_run = SyncRun(id=run_uuid, source=SOURCE, status="running")
                session.add(sync_run)

    try:
        paused = False
        with MarylandSdatConnector(raw_store, app_token=app_token, client=client) as connector:
            for page in connector.pages(limit=limit, where=where, cursor=cursor, page_number=next_page):
                validate_page_schema(page.records)
                validated = []
                for raw in page.records:
                    seen += 1
                    try:
                        validate_record(raw)
                        validated.append((raw, normalize_record(raw)))
                        validated_count += 1
                    except (RecordValidationError, ValueError, TypeError) as error:
                        failed += 1
                        logger.warning("maryland_record_failed", extra={"error": str(error)})
                if not dry_run and validated:
                    assert session_factory is not None
                    with session_factory.begin() as session:
                        for raw, normalized in validated:
                            _, was_created = store_record(
                                session,
                                raw,
                                normalized,
                                sync_run_id=run_uuid,
                                raw_file_path=str(page.raw_page.path),
                            )
                            created += int(was_created)
                            updated += int(not was_created)
                raw_store.write_checkpoint(
                    {
                        "cursor": page.cursor,
                        "next_page": int(page.raw_page.path.stem.split("-")[-1]) + 1,
                        "seen": seen,
                        "created": created,
                        "updated": updated,
                        "failed": failed,
                        "validated": validated_count,
                        "skipped": skipped,
                        "checkpoint_count": checkpoint_count + 1,
                        "elapsed_seconds": prior_elapsed + (time.monotonic() - started),
                    }
                )
                checkpoint_count += 1
                if max_pages is not None and connector.stats.pages_fetched >= max_pages:
                    paused = True
                    break
            connector_stats = connector.stats
        raw_store.write_manifest(source_url=API_URL)
        status = "paused" if paused else "succeeded" if failed == 0 else "completed_with_errors"
    except Exception as error:
        status = "failed"
        error_message = str(error)
        logger.exception("maryland_pipeline_failed")
        raise
    finally:
        if sync_run is not None and session_factory is not None:
            elapsed = prior_elapsed + (time.monotonic() - started)
            raw_bytes = sum(page.byte_count for page in raw_store.pages)
            metrics = {
                "county": county,
                "records_requested": limit,
                "records_per_second": seen / elapsed if elapsed else 0,
                "bytes_per_property_raw": raw_bytes / seen if seen else 0,
                "minimum_free_bytes": min_free_bytes,
            }
            with session_factory.begin() as session:
                persisted = session.get(SyncRun, run_uuid)
                if persisted:
                    from datetime import UTC, datetime

                    persisted.finished_at = datetime.now(UTC)
                    persisted.status = status
                    persisted.records_seen = seen
                    persisted.records_created = created
                    persisted.records_updated = updated
                    persisted.records_failed = failed
                    persisted.records_validated = validated_count
                    persisted.records_skipped = skipped
                    persisted.pages_fetched = prior_pages + connector_stats.pages_fetched
                    persisted.api_retries = prior_retries + connector_stats.retries
                    persisted.rate_limits = prior_rate_limits + connector_stats.rate_limits
                    persisted.server_errors = prior_server_errors + connector_stats.server_errors
                    persisted.raw_bytes = raw_bytes
                    persisted.checkpoint_count = checkpoint_count
                    persisted.elapsed_seconds = elapsed
                    persisted.metrics = metrics
                    persisted.error = error_message

    logger.info(
        "maryland_pipeline_finished",
        extra={
            "run_id": run_id,
            "records_seen": seen,
            "records_created": created,
            "records_updated": updated,
            "records_failed": failed,
        },
    )
    elapsed = prior_elapsed + (time.monotonic() - started)
    result_metrics = {
        "status": status,
        "county": county,
        "validated": validated_count,
        "skipped": skipped,
        "pages_fetched": prior_pages + connector_stats.pages_fetched,
        "api_retries": prior_retries + connector_stats.retries,
        "rate_limits": prior_rate_limits + connector_stats.rate_limits,
        "server_errors": prior_server_errors + connector_stats.server_errors,
        "raw_bytes": sum(page.byte_count for page in raw_store.pages),
        "checkpoint_count": checkpoint_count,
        "elapsed_seconds": elapsed,
        "records_per_second": seen / elapsed if elapsed else 0,
    }
    return PipelineResult(run_id, seen, created, updated, failed, raw_store.directory, result_metrics)
