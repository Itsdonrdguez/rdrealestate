from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging(settings.log_level)

app = FastAPI(
    title="Property Intelligence API",
    version="0.1.0",
    description="Local-first backend foundation for Maryland property intelligence.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Property Intelligence API"}
