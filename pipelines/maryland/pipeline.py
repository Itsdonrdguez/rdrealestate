from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.models import SyncRun

from .connector import MarylandSdatConnector
from .fields import API_URL, SOURCE
from .normalization import normalize_record
from .raw_store import RawStore
from .storage import store_record
from .validation import RecordValidationError, validate_record

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    seen: int
    created: int
    updated: int
    failed: int
    raw_directory: Path


def run_pipeline(
    session_factory: sessionmaker[Session] | None,
    *,
    raw_root: Path,
    app_token: str | None = None,
    limit: int | None = None,
    where: str | None = None,
    dry_run: bool = False,
    client=None,
) -> PipelineResult:
    run_uuid = uuid.uuid4()
    run_id = str(run_uuid)
    raw_store = RawStore(raw_root, run_id)
    seen = created = updated = failed = 0
    error_message: str | None = None

    sync_run: SyncRun | None = None
    if not dry_run:
        if session_factory is None:
            raise ValueError("session_factory is required unless dry_run is enabled")
        with session_factory.begin() as session:
            sync_run = SyncRun(id=run_uuid, source=SOURCE, status="running")
            session.add(sync_run)

    try:
        with MarylandSdatConnector(raw_store, app_token=app_token, client=client) as connector:
            for page in connector.pages(limit=limit, where=where):
                validated = []
                for raw in page.records:
                    seen += 1
                    try:
                        validate_record(raw)
                        validated.append((raw, normalize_record(raw)))
                    except (RecordValidationError, ValueError, TypeError) as error:
                        failed += 1
                        logger.warning("maryland_record_failed", extra={"error": str(error)})
                if not dry_run and validated:
                    assert session_factory is not None
                    with session_factory.begin() as session:
                        for raw, normalized in validated:
                            _, was_created = store_record(session, raw, normalized)
                            created += int(was_created)
                            updated += int(not was_created)
        raw_store.write_manifest(source_url=API_URL)
        status = "succeeded" if failed == 0 else "completed_with_errors"
    except Exception as error:
        status = "failed"
        error_message = str(error)
        logger.exception("maryland_pipeline_failed")
        raise
    finally:
        if sync_run is not None and session_factory is not None:
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
    return PipelineResult(run_id, seen, created, updated, failed, raw_store.directory)
