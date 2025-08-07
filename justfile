# Load environment variables from .env automatically
set dotenv-load := true

# cli interface
run address:
    poetry run python -m src.cli {{ address }}

runv address:
    poetry run python -m src.cli -v {{ address }}

t:
    just run 0xb1adceddb2941033a090dd166a462fe1c2029484

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
    #!/usr/bin/env bash
    set -euo pipefail

    # Kick off a job and capture the task id that the API returns
    task_id=$(curl -s -X POST http://localhost:8000/run \
        -H "Content-Type: application/json" \
        -d '{"address":"{{ address }}", "model":"gpt-4o"}' | \
        jq -r '.task_id')

    if [[ -z "${task_id}" || "${task_id}" == "null" ]]; then
        echo "Failed to obtain task_id from API response" >&2
        exit 1
    fi

    echo "Streaming events for task ${task_id}" >&2
    # -N disables buffering so events appear as they arrive
    curl -N http://localhost:8000/events/${task_id}

# docker
dc *command:
    docker compose {{ command }}


