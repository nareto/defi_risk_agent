# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

# Install system libs needed by psycopg2-binary, asyncpg, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc libpq-dev git curl && \
    rm -rf /var/lib/apt/lists/*

# Use a non-root user for safety
ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME=/opt/poetry \
    PATH="$POETRY_HOME/bin:$PATH"

# ---------- Install Poetry ----------
RUN curl -sSL https://install.python-poetry.org | python3 -  
ENV PATH="/opt/poetry/bin:$PATH"
RUN poetry config virtualenvs.create false

WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (without dev)
RUN poetry install --without dev

# Copy source code last (leverages Docker layer cache)
COPY . .

# Expose port
EXPOSE 8000

# Entrypoint relies on docker-compose overriding CMD/entrypoint
CMD ["poetry", "run", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
