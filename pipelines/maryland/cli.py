from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal

from .fields import COUNTY
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Maryland SDAT/MDP property records")
    parser.add_argument("--limit", type=int, default=100, help="Maximum records; omit with --all")
    parser.add_argument("--all", action="store_true", help="Process the entire statewide dataset")
    parser.add_argument("--where", help="Optional Socrata SoQL filter")
    parser.add_argument("--county", help="Exact county name, for example Charles")
    parser.add_argument("--dry-run", action="store_true", help="Extract, preserve, validate, and normalize only")
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--resume", metavar="RUN_ID", help="Resume from an existing run checkpoint")
    parser.add_argument("--min-free-gb", type=float, default=2.0, help="Reserved free disk space")
    parser.add_argument("--max-pages", type=int, help="Pause cleanly after this many pages")
    args = parser.parse_args()
    if args.county and args.where:
        parser.error("use either --county or --where, not both")
    escaped_county = args.county.replace("'", "''") if args.county else None
    where = f"{COUNTY}='{escaped_county}'" if escaped_county else args.where
    configure_logging(settings.log_level)
    result = run_pipeline(
        None if args.dry_run else SessionLocal,
        raw_root=args.raw_root,
        app_token=os.getenv("MARYLAND_APP_TOKEN") or None,
        limit=None if args.all else args.limit,
        where=where,
        dry_run=args.dry_run,
        resume_run_id=args.resume,
        min_free_bytes=int(args.min_free_gb * 1_000_000_000),
        max_pages=args.max_pages,
        county=args.county,
    )
    print(result)


if __name__ == "__main__":
    main()
