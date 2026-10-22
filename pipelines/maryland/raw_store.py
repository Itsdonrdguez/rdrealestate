from __future__ import annotations

import hashlib
import json
import shutil
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

    def __init__(self, root: Path, run_id: str, *, resume: bool = False, min_free_bytes: int = 0) -> None:
        self.directory = root / "maryland" / run_id
        self.directory.mkdir(parents=True, exist_ok=resume)
        self.min_free_bytes = min_free_bytes
        self.pages: list[RawPage] = []
        if resume:
            for path in sorted(self.directory.glob("page-*.json")):
                content = path.read_bytes()
                self.pages.append(RawPage(path, hashlib.sha256(content).hexdigest(), len(content), len(json.loads(content))))

    def save_page(self, page_number: int, content: bytes, record_count: int) -> RawPage:
        free = shutil.disk_usage(self.directory).free
        required = self.min_free_bytes + len(content)
        if free < required:
            raise OSError(f"insufficient disk space: {free} bytes free; {required} required")
        path = self.directory / f"page-{page_number:06d}.json"
        if path.exists():
            raise FileExistsError(f"raw page already exists: {path}")
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

    @property
    def checkpoint_path(self) -> Path:
        return self.directory / "checkpoint.json"

    def write_checkpoint(self, payload: dict[str, object]) -> None:
        temporary = self.directory / "checkpoint.tmp"
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.checkpoint_path)

    def read_checkpoint(self) -> dict[str, object]:
        return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
