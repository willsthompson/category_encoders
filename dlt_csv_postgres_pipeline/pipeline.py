"""
dlt pipeline that ingests CSV or Excel files and loads them into PostgreSQL.

Usage:
    uv run python pipeline.py <file_path> [--table <table_name>]

Environment variables:
    DESTINATION__POSTGRES__CREDENTIALS - Postgres connection string, e.g.:
        postgresql://user:password@localhost:5432/dbname
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterator

import dlt
from openpyxl import load_workbook


def _normalize_column(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def read_csv(file_path: Path) -> Iterator[dict]:
    """Yield rows from a CSV file as dicts with normalized column names."""
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {_normalize_column(k): v for k, v in row.items()}


def read_excel(file_path: Path) -> Iterator[dict]:
    """Yield rows from an Excel file as dicts with normalized column names."""
    wb = load_workbook(file_path, read_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = [_normalize_column(str(cell)) for cell in next(rows)]
    for row in rows:
        yield dict(zip(headers, row))
    wb.close()


READERS = {
    ".csv": read_csv,
    ".xlsx": read_excel,
    ".xls": read_excel,
}


@dlt.resource(
    write_disposition="replace",
    schema_contract="evolve",
)
def file_data(file_path: str, table_name: str) -> Iterator[dict]:
    """A dlt resource that yields rows from a CSV/Excel file."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    reader = READERS.get(suffix)
    if reader is None:
        raise ValueError(
            f"Unsupported file type: {suffix}. Supported: {', '.join(READERS)}"
        )
    yield from reader(path)


def run_pipeline(file_path: str, table_name: str) -> None:
    """Create and run the dlt pipeline."""
    pipeline = dlt.pipeline(
        pipeline_name="csv_to_postgres",
        destination="postgres",
        dataset_name="public_data",
    )

    data = file_data(file_path, table_name)
    data.table_name = table_name

    info = pipeline.run(data)
    print(f"Pipeline completed: {info}")


def main():
    parser = argparse.ArgumentParser(
        description="Load a CSV or Excel file into PostgreSQL using dlt"
    )
    parser.add_argument("file", help="Path to the CSV or Excel file")
    parser.add_argument(
        "--table",
        default=None,
        help="Target table name (defaults to the filename without extension)",
    )
    args = parser.parse_args()

    file_path = args.file
    if not Path(file_path).exists():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    table_name = args.table or Path(file_path).stem.lower().replace(" ", "_")

    print(f"Loading '{file_path}' into table '{table_name}'...")
    run_pipeline(file_path, table_name)


if __name__ == "__main__":
    main()
