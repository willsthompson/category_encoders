from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from core.config import settings
from core.pipeline import SUPPORTED_EXTENSIONS, run_pipeline

router = APIRouter()


class IngestResponse(BaseModel):
    table_name: str
    detail: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile, table_name: str | None = None):
    """Upload a CSV or Excel file and load it into PostgreSQL."""
    filename = file.filename or "upload.csv"
    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    resolved_table = table_name or Path(filename).stem.lower().replace(" ", "_")

    detail = run_pipeline(
        file=file.file,
        filename=filename,
        table_name=resolved_table,
        database_url=settings.database_url,
    )

    return IngestResponse(table_name=resolved_table, detail=detail)
