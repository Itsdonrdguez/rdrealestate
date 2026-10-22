from __future__ import annotations

import re
from dataclasses import dataclass

CORPORATE_SUFFIXES = (" L L C", " LLC", " INCORPORATED", " INC", " CORPORATION", " CORP", " L P", " LP")


def normalize_owner_name(value: str) -> str:
    normalized = " ".join(re.sub(r"[^A-Z0-9 ]", " ", value.upper()).split())
    for suffix in CORPORATE_SUFFIXES:
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)].strip()
    return normalized


def normalize_mailing_address(value: str) -> str:
    return " ".join(re.sub(r"[^A-Z0-9 ]", " ", value.upper()).split())


@dataclass(frozen=True)
class OwnerIdentity:
    normalized_name: str
    normalized_mailing_address: str | None


@dataclass(frozen=True)
class MatchDecision:
    matched: bool
    status: str
    method: str
    confidence: float


def match_owner(candidate: OwnerIdentity, existing: OwnerIdentity) -> MatchDecision:
    if candidate.normalized_name != existing.normalized_name:
        return MatchDecision(False, "rejected", "name_mismatch", 0.0)
    if candidate.normalized_mailing_address and candidate.normalized_mailing_address == existing.normalized_mailing_address:
        return MatchDecision(True, "confirmed", "exact_name_and_mailing_address", 1.0)
    return MatchDecision(False, "candidate", "exact_name_only", 0.5)
