FROM python:3.11-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml .
RUN uv sync --no-dev

COPY . .

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
