from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.intelligence import router as intelligence_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging(settings.log_level)

app = FastAPI(
    title="Property Intelligence API",
    version="0.1.0",
    description="Local-first backend foundation for Maryland property intelligence.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(intelligence_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Property Intelligence API"}
