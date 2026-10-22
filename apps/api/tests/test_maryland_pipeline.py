import json
from decimal import Decimal

import httpx
import pytest

from pipelines.maryland import fields
from pipelines.maryland.connector import MarylandSdatConnector
from pipelines.maryland.normalization import normalize_record
from pipelines.maryland.pipeline import run_pipeline
from pipelines.maryland.raw_store import RawStore
from pipelines.maryland.validation import RecordValidationError, SchemaDriftError, validate_page_schema, validate_record


@pytest.fixture
def maryland_record() -> dict[str, object]:
    return {
        fields.JURISDICTION: "ALLE",
        fields.COUNTY: "Allegany",
        fields.ACCOUNT_ID: "0101088483",
        fields.ADDRESS: "11105  JOHN O PRICE RD NE",
        fields.CITY: "LITTLE ORLEANS",
        fields.ZIP_CODE: "21766",
        fields.STREET_NUMBER: "11105",
        fields.STREET_NAME: "JOHN O PRICE",
        fields.STREET_TYPE: "RD",
        fields.LATITUDE: "39.679463",
        fields.LONGITUDE: "-78.367726",
        fields.PROPERTY_TYPE: "SF",
        fields.LAND_USE: "Residential (R)",
        fields.YEAR_BUILT: "1993",
        fields.SQUARE_FEET: "1620",
        fields.ASSESSED_VALUE: "198900",
        fields.ASSESSMENT_YEAR: "2027",
        fields.SALE_DATE: "1981.10.13",
        fields.SALE_PRICE: "900",
        fields.OWNER_OCCUPANCY: "H",
        fields.LAST_UPDATED: "20261005",
    }


def test_validation_reports_missing_source_identity() -> None:
    with pytest.raises(RecordValidationError) as error:
        validate_record({fields.COUNTY: "Allegany"})
    assert fields.ACCOUNT_ID in str(error.value)


def test_schema_drift_stops_a_page_before_storage() -> None:
    with pytest.raises(SchemaDriftError):
        validate_page_schema([{fields.ACCOUNT_ID: "one"}])


def test_connector_uses_keyset_cursor(tmp_path, maryland_record: dict[str, object]) -> None:
    requests: list[httpx.Request] = []
    first = {**maryland_record, fields.ACCOUNT_ID: "10"}

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = [first] if len(requests) == 1 else []
        return httpx.Response(200, json=body)

    store = RawStore(tmp_path, "keyset")
    connector = MarylandSdatConnector(store, client=httpx.Client(transport=httpx.MockTransport(handler)), page_size=1)
    pages = list(connector.pages())
    assert pages[0].cursor == "10"
    assert f"{fields.ACCOUNT_ID} > '10'" in requests[1].url.params["$where"]


def test_normalization_does_not_mutate_raw_record(maryland_record: dict[str, object]) -> None:
    before = maryland_record.copy()
    normalized = normalize_record(maryland_record)
    assert maryland_record == before
    assert normalized.source_identifier == "0101088483"
    assert normalized.normalized_address == "11105 JOHN O PRICE RD NE LITTLE ORLEANS MD 21766"
    assert normalized.assessed_value == Decimal("198900")
    assert normalized.sale_price == Decimal("900")
    assert normalized.owner_occupied is True


def test_connector_preserves_exact_response_bytes(tmp_path, maryland_record: dict[str, object]) -> None:
    content = json.dumps([maryland_record], separators=(", ", ": ")).encode()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["$order"] == f"{fields.ACCOUNT_ID} ASC"
        return httpx.Response(200, content=content, headers={"content-type": "application/json"})

    raw_store = RawStore(tmp_path, "test-run")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    connector = MarylandSdatConnector(raw_store, client=client, page_size=10)
    page = next(connector.pages(limit=1))
    assert page.records == [maryland_record]
    assert page.raw_page.path.read_bytes() == content


def test_dry_run_extracts_validates_and_writes_manifest(tmp_path, maryland_record: dict[str, object]) -> None:
    content = json.dumps([maryland_record]).encode()
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=content)))
    result = run_pipeline(None, raw_root=tmp_path, limit=1, dry_run=True, client=client)
    assert result.seen == 1
    assert result.failed == 0
    assert (result.raw_directory / "page-000001.json").read_bytes() == content
    assert (result.raw_directory / "manifest.json").exists()
