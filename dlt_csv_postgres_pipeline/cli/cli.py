"""
CLI for the dlt ingestion API.

Wraps the generated httpx client with typer commands.
After API changes, regenerate the client with:
    python scripts/generate_client.py
"""

import sys
from pathlib import Path
from typing import Annotated, Optional

import httpx
import typer

app = typer.Typer(help="dlt CSV/Excel ingestion CLI")

DEFAULT_API_URL = "http://localhost:8000"


def _api_url() -> str:
    import os

    return os.environ.get("API_URL", DEFAULT_API_URL)


@app.command()
def ingest(
    file: Annotated[Path, typer.Argument(help="Path to CSV or Excel file")],
    table_name: Annotated[
        Optional[str],
        typer.Option("--table", "-t", help="Target table name"),
    ] = None,
):
    """Upload a file to the ingestion API."""
    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    url = f"{_api_url()}/ingest"
    params = {}
    if table_name:
        params["table_name"] = table_name

    with open(file, "rb") as f:
        response = httpx.post(
            url,
            files={"file": (file.name, f)},
            params=params,
            timeout=300,
        )

    if response.status_code != 200:
        typer.echo(f"Error ({response.status_code}): {response.text}", err=True)
        raise typer.Exit(1)

    result = response.json()
    typer.echo(f"Loaded into table '{result['table_name']}'")
    typer.echo(result["detail"])


@app.command()
def health():
    """Check if the API is reachable."""
    try:
        response = httpx.get(f"{_api_url()}/health", timeout=5)
        response.raise_for_status()
        typer.echo("API is healthy")
    except httpx.HTTPError as e:
        typer.echo(f"API unreachable: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
