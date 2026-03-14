#!/usr/bin/env python
"""
Generate the CLI client SDK from the FastAPI app's OpenAPI spec.

Usage:
    python scripts/generate_client.py

Imports the FastAPI app directly (no running server needed),
writes the OpenAPI spec to openapi.json, and runs
openapi-python-client to generate a typed httpx client.
"""

import json
import subprocess
import sys
from pathlib import Path

# Ensure the api/ package is importable
ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "api"
sys.path.insert(0, str(API_DIR))

from main import app  # noqa: E402

SPEC_PATH = ROOT / "openapi.json"
OUTPUT_PATH = ROOT / "cli" / "generated"


def main() -> None:
    spec = app.openapi()
    SPEC_PATH.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"Wrote OpenAPI spec to {SPEC_PATH}")

    cmd = [
        sys.executable, "-m", "openapi_python_client",
        "generate",
        "--path", str(SPEC_PATH),
        "--output-path", str(OUTPUT_PATH),
        "--overwrite",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print("Client generation failed", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"Generated client at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
