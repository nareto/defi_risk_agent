run address:
    poetry run python -m src.cli {{ address }}

runv address:
    poetry run python -m src.cli -v {{ address }}

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
