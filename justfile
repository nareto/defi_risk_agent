run address:
    poetry run -m src.main -v {{ address }}

brun:
    ./batch_run.sh

# poetry run pytest --ipdb
test:
    poetry run pytest tests/ "${@}"  --pdb --pdbcls=IPython.core.debugger:Pdb -sx

langsmith:
    docker-compose -f docker-compose.langsmith.yml up 