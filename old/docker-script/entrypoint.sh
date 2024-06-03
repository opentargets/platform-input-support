#!/bin/sh

echo "[GCP] Activate the provided service account"
gcloud auth activate-service-account --key-file=/srv/credentials/open-targets-gac.json

echo "[PIS] Running Platform input support with parameters $*"
poetry run python3 platform-input-support.py "$@"

exit $!