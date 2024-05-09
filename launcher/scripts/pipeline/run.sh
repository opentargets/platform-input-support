#!/bin/bash

config=$(realpath "${OTOPS_PATH_PIS_CONFIG}")
output=$(realpath "${OTOPS_PATH_PIS_OUTPUT_DIR}")
logs=$(realpath "${OTOPS_PATH_PIS_LOGS_DIR}")
creds=$(realpath "${OTOPS_PATH_GCS_CREDENTIALS_FILE}")
#Removing outermost quotes
pis_args="${OTOPS_PIS_RUN_ARGS#\"}"
pis_args="${pis_args%\"}"

gb_arg_line=

params=$(getopt -o n --long nogcp -- "$@")
eval set -- "$params"
unset params

case $1 in
  -n|--nogcp)
    gb_arg_line=""
    ;;
  --)
    gb_arg_line="-gb ${OTOPS_PATH_GCS_PIS_OUTPUT}"
    upload_logs=true
    ;;
esac


run_cmd="docker run \
         -v ${output}:/srv/output \
         -v ${logs}:/usr/src/app/log \
         -v ${creds}:/srv/credentials/open-targets-gac.json \
         -v ${config}:/usr/src/app/config.yaml
         ${OTOPS_PIS_DOCKER_IMAGE_NAME}:${OTOPS_PIS_DOCKER_IMAGE_TAG} \
         -o /srv/output \
         --log-level=DEBUG \
         -gkey /srv/credentials/open-targets-gac.json \
         $gb_arg_line \
         $pis_args"

$run_cmd

if [ -n "$upload_logs" ]; then
  gsutil -m rsync -r "${logs}"/ "${OTOPS_PATH_GCS_PIS_SESSION_LOGS}"
fi
