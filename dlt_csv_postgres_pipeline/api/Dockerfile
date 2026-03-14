FROM python:3.11-slim

RUN pip install uv

WORKDIR /app

COPY api/pyproject.toml .
RUN uv sync --no-dev

COPY core/ ./core/
COPY api/ ./

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
