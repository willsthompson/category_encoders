"""
dlt ingestion logic — the shared domain core.

No framework imports (no FastAPI, no typer, no SQS SDK).
Any interface (HTTP, CLI, queue consumer) calls run_pipeline().
"""

import csv
import io
import tempfile
from pathlib import Path
from typing import BinaryIO, Iterator

import dlt
import pyarrow as pa
from openpyxl import load_workbook

BATCH_SIZE = 10_000

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def _normalize_column(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _rows_to_arrow(headers: list[str], rows: list[list]) -> pa.Table:
    columns = list(zip(*rows)) if rows else [[] for _ in headers]
    arrays = [pa.array(col) for col in columns]
    return pa.table(dict(zip(headers, arrays)))


def _read_csv(f: io.TextIOWrapper) -> Iterator[pa.Table]:
    reader = csv.reader(f)
    raw_headers = next(reader)
    headers = [_normalize_column(h) for h in raw_headers]

    batch: list[list] = []
    for row in reader:
        batch.append(row)
        if len(batch) >= BATCH_SIZE:
            yield _rows_to_arrow(headers, batch)
            batch = []
    if batch:
        yield _rows_to_arrow(headers, batch)


def _read_excel(path: Path) -> Iterator[pa.Table]:
    wb = load_workbook(path, read_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = [_normalize_column(str(cell)) for cell in next(rows)]

    batch: list[list] = []
    for row in rows:
        batch.append(list(row))
        if len(batch) >= BATCH_SIZE:
            yield _rows_to_arrow(headers, batch)
            batch = []
    if batch:
        yield _rows_to_arrow(headers, batch)
    wb.close()


@dlt.resource(write_disposition="replace", schema_contract="evolve")
def _file_resource(
    file: BinaryIO, filename: str, table_name: str
) -> Iterator[pa.Table]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        text = io.TextIOWrapper(file, encoding="utf-8")
        yield from _read_csv(text)
    elif suffix in (".xlsx", ".xls"):
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file.read())
            tmp_path = Path(tmp.name)
        try:
            yield from _read_excel(tmp_path)
        finally:
            tmp_path.unlink()
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )


def run_pipeline(
    file: BinaryIO, filename: str, table_name: str, database_url: str
) -> str:
    """Run the dlt pipeline and return a summary string."""
    import os

    os.environ["DESTINATION__POSTGRES__CREDENTIALS"] = database_url

    pipeline = dlt.pipeline(
        pipeline_name="csv_to_postgres",
        destination="postgres",
        dataset_name="public_data",
    )

    data = _file_resource(file, filename, table_name)
    data.table_name = table_name

    info = pipeline.run(data)
    return str(info)
