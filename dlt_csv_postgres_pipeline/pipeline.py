"""
dlt pipeline that ingests CSV or Excel files and loads them into PostgreSQL.

Usage:
    python pipeline.py <file_path> [--table <table_name>]

Environment variables:
    DESTINATION__POSTGRES__CREDENTIALS - Postgres connection string, e.g.:
        postgresql://user:password@localhost:5432/dbname
"""

import argparse
import sys
from pathlib import Path

import dlt
import pandas as pd


def read_file(file_path: str) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)
    elif suffix in (".xls", ".xlsx"):
        return pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .csv, .xls, or .xlsx")


@dlt.resource(write_disposition="replace")
def file_data(file_path: str, table_name: str):
    """A dlt resource that yields rows from a CSV/Excel file."""
    df = read_file(file_path)
    # Normalize column names: lowercase, replace spaces with underscores
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    yield from df.to_dict(orient="records")


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
