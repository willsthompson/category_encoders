# dlt CSV/Excel to PostgreSQL Pipeline

A simple [dlt](https://dlthub.com/) pipeline that loads CSV or Excel files into a PostgreSQL database.

## Setup

```bash
uv sync
```

## Configure PostgreSQL Connection

Set the connection string as an environment variable:

```bash
export DESTINATION__POSTGRES__CREDENTIALS="postgresql://user:password@localhost:5432/mydb"
```

Or create a `.dlt/secrets.toml` file in this directory:

```toml
[destination.postgres.credentials]
database = "mydb"
username = "user"
password = "password"
host = "localhost"
port = 5432
```

## Usage

Load a CSV file:

```bash
uv run python pipeline.py sample_data.csv
```

Load an Excel file with a custom table name:

```bash
uv run python pipeline.py data.xlsx --table employees
```

The pipeline will:
1. Read the CSV or Excel file using pandas
2. Normalize column names (lowercase, underscores)
3. Load all rows into the specified PostgreSQL table using `replace` write disposition
