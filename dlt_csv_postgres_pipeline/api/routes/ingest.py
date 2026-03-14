from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from core.config import settings
from core.pipeline import derive_table_name, run_pipeline

router = APIRouter()


class IngestResponse(BaseModel):
    table_name: str
    detail: str


@router.post("/ingest", response_model=IngestResponse)
def ingest(file: UploadFile, table_name: str | None = None):
    """Upload a CSV or Excel file and load it into PostgreSQL."""
    filename = file.filename or "upload.csv"
    resolved_table = table_name or derive_table_name(filename)

    try:
        detail = run_pipeline(
            file=file.file,
            filename=filename,
            table_name=resolved_table,
            database_url=settings.database_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return IngestResponse(table_name=resolved_table, detail=detail)
