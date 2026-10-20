import json
import logging

from app.core.logging import JsonFormatter


def test_json_formatter_emits_structured_log() -> None:
    record = logging.LogRecord("pipeline", logging.INFO, __file__, 1, "stored %s", (3,), None)
    record.run_id = "test-run"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "pipeline"
    assert payload["message"] == "stored 3"
    assert payload["timestamp"].endswith("+00:00")
    assert payload["run_id"] == "test-run"
