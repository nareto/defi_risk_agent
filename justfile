run address:
    poetry run python -m src.cli {{ address }}

debug address:
    poetry run python -m ipdb -c continue -m src.cli -v {{ address }}

brun:
    ./batch_run.sh

# poetry run pytest --ipdb
test:
    poetry run pytest tests/ "${@}"  --pdb --pdbcls=IPython.core.debugger:Pdb -sx
