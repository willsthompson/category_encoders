import os
from pathlib import Path

import dlt
from pytest_postgresql import factories

from pipeline import file_data

postgresql_proc = factories.postgresql_proc()
postgresql = factories.postgresql("postgresql_proc")


def test_csv_loads_into_postgres(postgresql, tmp_path):
    """CSV data is loaded into Postgres with correct rows and columns."""
    # Write a small test CSV
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "id,name,department\n"
        "1,Alice,Engineering\n"
        "2,Bob,Marketing\n"
        "3,Carol,Sales\n"
    )

    # Build connection string from the fixture
    info = postgresql.info
    credentials = f"postgresql://{info.user}:@{info.host}:{info.port}/{info.dbname}"
    os.environ["DESTINATION__POSTGRES__CREDENTIALS"] = credentials

    # Run the pipeline
    pipeline = dlt.pipeline(
        pipeline_name="test_csv",
        destination="postgres",
        dataset_name="test_data",
    )
    data = file_data(str(csv_file), "employees")
    data.table_name = "employees"
    pipeline.run(data)

    # Verify rows landed
    with postgresql.cursor() as cur:
        cur.execute("SELECT id, name, department FROM test_data.employees ORDER BY id")
        rows = cur.fetchall()

    assert len(rows) == 3
    assert rows[0] == ("1", "Alice", "Engineering")
    assert rows[1] == ("2", "Bob", "Marketing")
    assert rows[2] == ("3", "Carol", "Sales")
