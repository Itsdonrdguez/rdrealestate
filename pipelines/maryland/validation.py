from __future__ import annotations

from dataclasses import dataclass

from .fields import ACCOUNT_ID, REQUIRED_FIELDS


@dataclass(frozen=True)
class RecordValidationError(ValueError):
    source_identifier: str | None
    errors: tuple[str, ...]

    def __str__(self) -> str:
        return f"record {self.source_identifier or '<unknown>'}: {'; '.join(self.errors)}"


def validate_record(record: dict[str, object]) -> None:
    errors = tuple(f"missing required field: {field}" for field in REQUIRED_FIELDS if not record.get(field))
    if errors:
        identifier = str(record.get(ACCOUNT_ID)) if record.get(ACCOUNT_ID) else None
        raise RecordValidationError(identifier, errors)
