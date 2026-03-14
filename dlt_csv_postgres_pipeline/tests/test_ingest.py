"""
Integration tests for the /ingest endpoint.

Uses pytest-postgresql for a real Postgres instance and
FastAPI's TestClient for HTTP-level testing.
"""

import io
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from pytest_postgresql import factories

# Both api/ and the project root must be on sys.path so that
# `from core.*` and `from routes.*` resolve correctly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from main import app  # noqa: E402

postgresql_proc = factories.postgresql_proc()
postgresql = factories.postgresql("postgresql_proc")

EXPECTED_ROWS = [
    ("1", "Alice", "Engineering"),
    ("2", "Bob", "Marketing"),
    ("3", "Carol", "Sales"),
]

CSV_CONTENT = (
    "id,name,department\n"
    "1,Alice,Engineering\n"
    "2,Bob,Marketing\n"
    "3,Carol,Sales\n"
)


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_csv(postgresql):
    info = postgresql.info
    db_url = f"postgresql://{info.user}:@{info.host}:{info.port}/{info.dbname}"
    os.environ["DATABASE_URL"] = db_url

    from core.config import Settings

    import routes.ingest as ingest_mod

    ingest_mod.settings = Settings()

    client = TestClient(app)
    response = client.post(
        "/ingest",
        files={"file": ("test.csv", io.BytesIO(CSV_CONTENT.encode()), "text/csv")},
        params={"table_name": "employees"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["table_name"] == "employees"

    with postgresql.cursor() as cur:
        cur.execute(
            "SELECT id, name, department FROM public_data.employees ORDER BY id"
        )
        rows = cur.fetchall()

    assert len(rows) == 3
    for actual, expected in zip(rows, EXPECTED_ROWS):
        assert tuple(str(v) for v in actual) == expected


def test_ingest_rejects_unsupported_type():
    client = TestClient(app)
    response = client.post(
        "/ingest",
        files={"file": ("data.json", io.BytesIO(b"{}"), "application/json")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
