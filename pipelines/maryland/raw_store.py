from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class RawPage:
    path: Path
    sha256: str
    byte_count: int
    record_count: int


class RawStore:
    """Append-only storage for exact HTTP response bodies."""

    def __init__(self, root: Path, run_id: str) -> None:
        self.directory = root / "maryland" / run_id
        self.directory.mkdir(parents=True, exist_ok=False)
        self.pages: list[RawPage] = []

    def save_page(self, page_number: int, content: bytes, record_count: int) -> RawPage:
        path = self.directory / f"page-{page_number:06d}.json"
        path.write_bytes(content)
        page = RawPage(path, hashlib.sha256(content).hexdigest(), len(content), record_count)
        self.pages.append(page)
        return page

    def write_manifest(self, *, source_url: str) -> Path:
        path = self.directory / "manifest.json"
        payload = {
            "created_at": datetime.now(UTC).isoformat(),
            "source_url": source_url,
            "pages": [{**asdict(page), "path": page.path.name} for page in self.pages],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
