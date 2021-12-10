#!/bin/sh

echo "Running Platform input support with parameters $*"
conda run --no-capture-output -n pis-py3.8 python3 platform-input-support.py "$@"

exit $!