#!/bin/bash
# Common configuration for all scripts, including a common toolset

# Bootstrapping environment
SCRIPTDIR="$( cd "$( dirname "$${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Environment variables
export pis_path_pipeline_root=${PIS_PATH_PIPELINE_ROOT}
export pis_path_pipeline_scripts=${PIS_PATH_PIPELINE_SCRIPTS}
export pis_filename_pipeline_scripts_entry_point=${PIS_FILENAME_PIPELINE_SCRIPTS_ENTRY_POINT}

# Log folders
export pis_path_logs_pis="$${pis_path_logs_pipeline}/pis"
export pis_path_logs_startup_script="$${pis_path_logs_pis}/startup_script.log"
# Temporary folders
export pis_path_tmp="${PIS_PATH_PIPELINE_ROOT}/tmp"
# List of folders that need to exist for the pipeline scripts to run
export pis_list_folders_pipeline="$${pis_path_logs_pipeline} $${pis_path_logs_pis} $${pis_path_tmp}"

# Helper functions
# Logging helper function
function log() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@"
}

function logf() {
  log "$@" | tee -a $${pis_path_logs_startup_script}
}

# Print a summary with the running environment (all environment variables starting with PIS_)
function env_summary() {
  log "[GLOBAL] Environment summary:"
  for var in $(compgen -e | grep pis_); do
    log "  - $${var} = $${!var}"
  done
}

# Ensure that the list of folders that need to exist for the pipeline scripts to run exist
function ensure_folders_exist() {
  for folder in $${pis_list_folders_pipeline}; do
    if [[ ! -d $${folder} ]]; then
      log "Creating folder $${folder}"
      mkdir -p $${folder}
    fi
  done
}

# Common environment summary
env_summary