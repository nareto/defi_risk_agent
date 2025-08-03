# Load environment variables from .env automatically
set dotenv-load := true

# cli interface
run address:
    poetry run python -m src.cli {{ address }}

runv address:
    poetry run python -m src.cli -v {{ address }}

runl address:
    poetry run python -m src.cli -v {{ address }} > runs_output/{{ address }}.$(date -u +"%Y-%m-%dT%H-%M-%SZ").log 2>&1

resume threadturn:
    poetry run python -m src.cli --resume-from {{ threadturn }}

resumev threadturn:
    poetry run python -m src.cli -v --resume-from {{ threadturn }}

debug address:
    poetry run python -m ipdb -c continue -m src.cli -v {{ address }}

brun:
    ./batch_run.sh

# poetry run pytest --ipdb
test:
    poetry run pytest tests/ "${@}"  --pdb --pdbcls=IPython.core.debugger:Pdb -sx

resume_last turn:
    #!/usr/bin/env bash
    set -euo pipefail
    latest_dir=$(ls -1 runs_output | grep '^state_' | tail -n 1)
    statefile="runs_output/${latest_dir}/turn_{{turn}}.json"
    just resume "${statefile}"

# backend 
backend:
    just dc up -d db 
    just dc up -d redis
    DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:15432/${POSTGRES_DB} \
        poetry run uvicorn src.server:app --reload

tbackend address:
    #!/bin/bash
    # Start a job
    curl -X POST http://localhost:8000/run -H "Content-Type: application/json" \
        -d '{"address":"{{ address }}", "model":"gpt-4o"}'

    # Stream progress
    curl http://localhost:8000/events/<TASK_ID>

# docker
dc *command:
    docker compose {{ command }}
