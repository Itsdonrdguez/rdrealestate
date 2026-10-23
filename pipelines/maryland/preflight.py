from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .fields import API_URL, COUNTY


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def collect_preflight(repository_root: Path, county: str, minimum_free_bytes: int) -> dict[str, object]:
    disk = shutil.disk_usage(repository_root)
    escaped = county.replace("'", "''")
    response = httpx.get(
        API_URL,
        params={"$select": "count(*) as count", "$where": f"{COUNTY}='{escaped}'"},
        timeout=60,
    )
    response.raise_for_status()
    county_records = int(response.json()[0]["count"])
    statewide_response = httpx.get(
        API_URL,
        params={"$select": "count(*) as count"},
        timeout=60,
    )
    statewide_response.raise_for_status()
    statewide_records = int(statewide_response.json()[0]["count"])
    database_result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "sh",
            "-c",
            'psql -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
            "-c 'SELECT pg_database_size(current_database())'",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    database_bytes = int(database_result.stdout.strip())
    docker_usage = subprocess.run(
        ["docker", "system", "df"], check=True, capture_output=True, text=True
    ).stdout.strip()
    raw_root = repository_root / "data" / "raw"
    return {
        "measured_at": datetime.now(UTC).isoformat(),
        "county": county,
        "county_records": county_records,
        "statewide_records": statewide_records,
        "host_total_bytes": disk.total,
        "host_used_bytes": disk.used,
        "host_free_bytes": disk.free,
        "minimum_free_bytes": minimum_free_bytes,
        "available_above_threshold_bytes": max(0, disk.free - minimum_free_bytes),
        "raw_directory_bytes": directory_size(raw_root),
        "database_bytes": database_bytes,
        "docker_system_df": docker_usage,
        "preflight_passed": disk.free > minimum_free_bytes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Maryland county-ingestion capacity preflight")
    parser.add_argument("--county", default="Charles")
    parser.add_argument("--min-free-gb", type=float, default=2.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repository_root = Path(__file__).resolve().parents[2]
    result = collect_preflight(repository_root, args.county, int(args.min_free_gb * 1_000_000_000))
    output = args.output or repository_root / "data" / "exports" / f"{args.county.lower()}-preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["preflight_passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
