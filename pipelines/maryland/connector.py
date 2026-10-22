from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass

import httpx

from .fields import ACCOUNT_ID, API_URL
from .raw_store import RawPage, RawStore


@dataclass(frozen=True)
class ExtractedPage:
    records: list[dict[str, object]]
    raw_page: RawPage
    cursor: str | None


class MarylandSdatConnector:
    """Read-only Socrata connector; it never mutates the database."""

    def __init__(
        self,
        raw_store: RawStore,
        *,
        app_token: str | None = None,
        client: httpx.Client | None = None,
        page_size: int = 1_000,
        max_retries: int = 5,
    ) -> None:
        self.raw_store = raw_store
        self.page_size = page_size
        self.max_retries = max_retries
        headers = {"X-App-Token": app_token} if app_token else {}
        self.client = client or httpx.Client(headers=headers, timeout=60.0)
        self._owns_client = client is None

    def pages(
        self,
        *,
        limit: int | None = None,
        where: str | None = None,
        cursor: str | None = None,
        page_number: int = 1,
    ) -> Iterator[ExtractedPage]:
        remaining = limit
        while remaining is None or remaining > 0:
            requested = self.page_size if remaining is None else min(self.page_size, remaining)
            params: dict[str, str | int] = {
                "$limit": requested,
                "$order": f"{ACCOUNT_ID} ASC",
            }
            filters = [f"{ACCOUNT_ID} > '{cursor}'"] if cursor else []
            if where:
                filters.append(f"({where})")
            if filters:
                params["$where"] = " AND ".join(filters)
            response = self._get(params)
            records = json.loads(response.content)
            if not isinstance(records, list):
                raise ValueError("Maryland API response must be a JSON array")
            raw_page = self.raw_store.save_page(page_number, response.content, len(records))
            next_cursor = str(records[-1].get(ACCOUNT_ID)) if records else cursor
            yield ExtractedPage(records, raw_page, next_cursor)
            count = len(records)
            if count < requested:
                break
            if count and not next_cursor:
                raise ValueError("Maryland API page is missing the account ID keyset cursor")
            cursor = next_cursor
            page_number += 1
            if remaining is not None:
                remaining -= count

    def _get(self, params: dict[str, str | int]) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.get(API_URL, params=params)
            except httpx.TransportError:
                if attempt >= self.max_retries:
                    raise
                time.sleep(min(0.5 * (2**attempt), 8.0))
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt >= self.max_retries:
                    response.raise_for_status()
                time.sleep(min(0.5 * (2**attempt), 8.0))
                continue
            response.raise_for_status()
            return response
        raise RuntimeError("unreachable")

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> "MarylandSdatConnector":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
