from fastapi import FastAPI

from routes.health import router as health_router
from routes.ingest import router as ingest_router

app = FastAPI(title="dlt CSV/Excel Ingestion API", version="0.1.0")

app.include_router(health_router)
app.include_router(ingest_router)
