import os
from pathlib import Path

import dlt
import pytest
from openpyxl import Workbook
from pytest_postgresql import factories

from pipeline import file_data

postgresql_proc = factories.postgresql_proc()
postgresql = factories.postgresql("postgresql_proc")

EXPECTED_ROWS = [
    ("1", "Alice", "Engineering"),
    ("2", "Bob", "Marketing"),
    ("3", "Carol", "Sales"),
]


def _write_csv(path: Path) -> Path:
    f = path / "test.csv"
    f.write_text(
        "id,name,department\n"
        "1,Alice,Engineering\n"
        "2,Bob,Marketing\n"
        "3,Carol,Sales\n"
    )
    return f


def _write_excel(path: Path) -> Path:
    f = path / "test.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["id", "name", "department"])
    ws.append([1, "Alice", "Engineering"])
    ws.append([2, "Bob", "Marketing"])
    ws.append([3, "Carol", "Sales"])
    wb.save(f)
    return f


@pytest.mark.parametrize("write_file", [_write_csv, _write_excel], ids=["csv", "xlsx"])
def test_file_loads_into_postgres(postgresql, tmp_path, write_file):
    """File data is loaded into Postgres with correct rows and columns."""
    test_file = write_file(tmp_path)

    info = postgresql.info
    credentials = f"postgresql://{info.user}:@{info.host}:{info.port}/{info.dbname}"
    os.environ["DESTINATION__POSTGRES__CREDENTIALS"] = credentials

    pipeline = dlt.pipeline(
        pipeline_name=f"test_{test_file.suffix.lstrip('.')}",
        destination="postgres",
        dataset_name="test_data",
    )
    data = file_data(str(test_file), "employees")
    data.table_name = "employees"
    pipeline.run(data)

    with postgresql.cursor() as cur:
        cur.execute("SELECT id, name, department FROM test_data.employees ORDER BY id")
        rows = cur.fetchall()

    assert len(rows) == 3
    for actual, expected in zip(rows, EXPECTED_ROWS):
        # Excel may load ints; coerce to str for uniform comparison
        assert tuple(str(v) for v in actual) == expected
