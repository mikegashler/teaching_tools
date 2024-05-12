#!/bin/bash
set -e
echo "Type-checking the back end"
pushd back_end
mypy main.py --strict --implicit-reexport --ignore-missing-imports
echo "Running"
python3 main.py open_browser
popd
echo "Done"
