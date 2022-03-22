#!/bin/sh

echo "[GCP] Activate the provided service account"
gcloud auth activate-service-account --key-file=/srv/credentials/open-targets-gac.json

echo "[PIS] Running Platform input support with parameters $*"
conda run --no-capture-output -n pis-py3.8 python3 platform-input-support.py "$@"

exit $!