from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

import httpx

from .fields import API_URL
from .raw_store import RawPage, RawStore


@dataclass(frozen=True)
class ExtractedPage:
    records: list[dict[str, object]]
    raw_page: RawPage


class MarylandSdatConnector:
    """Read-only Socrata connector; it never mutates the database."""

    def __init__(
        self,
        raw_store: RawStore,
        *,
        app_token: str | None = None,
        client: httpx.Client | None = None,
        page_size: int = 1_000,
    ) -> None:
        self.raw_store = raw_store
        self.page_size = page_size
        headers = {"X-App-Token": app_token} if app_token else {}
        self.client = client or httpx.Client(headers=headers, timeout=60.0)
        self._owns_client = client is None

    def pages(self, *, limit: int | None = None, where: str | None = None) -> Iterator[ExtractedPage]:
        offset = 0
        page_number = 1
        remaining = limit
        while remaining is None or remaining > 0:
            requested = self.page_size if remaining is None else min(self.page_size, remaining)
            params: dict[str, str | int] = {
                "$limit": requested,
                "$offset": offset,
                "$order": ":id",
            }
            if where:
                params["$where"] = where
            response = self.client.get(API_URL, params=params)
            response.raise_for_status()
            records = json.loads(response.content)
            if not isinstance(records, list):
                raise ValueError("Maryland API response must be a JSON array")
            raw_page = self.raw_store.save_page(page_number, response.content, len(records))
            yield ExtractedPage(records, raw_page)
            count = len(records)
            if count < requested:
                break
            offset += count
            page_number += 1
            if remaining is not None:
                remaining -= count

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> "MarylandSdatConnector":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
