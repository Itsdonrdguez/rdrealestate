import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Small JSON formatter suitable for local pipeline and API logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        standard = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}
        payload.update({key: value for key, value in record.__dict__.items() if key not in standard})
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)
