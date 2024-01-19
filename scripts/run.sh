#!/bin/bash

config=$(realpath "${config_dest}/config.yaml")
output=$(realpath ${OTOPS_PATH_PIS_OUTPUT_DIR})
logs=$(realpath ${OTOPS_PATH_PIS_LOGS_DIR})
creds=$(realpath ${OTOPS_PATH_GCS_CREDENTIALS_FILE})

run_cmd="docker run \
         -v ${output}:/srv/output \
         -v ${logs}:/usr/src/app/log \
         -v ${creds}:/srv/credentials/open-targets-gac.json \
         -v ${config}:/usr/src/app/config.yaml
         ${OTOPS_PIS_DOCKER_IMAGE_NAME}:${OTOPS_PIS_DOCKER_IMAGE_TAG} \
         -o /srv/output \
         --log-level=DEBUG \
         -gkey /srv/credentials/open-targets-gac.json \
         -gb ${OTOPS_PATH_GCS_PIS_OUTPUT} \
         $@"

$run_cmd
