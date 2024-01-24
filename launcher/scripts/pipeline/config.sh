#!/bin/bash
# Common configuration for all scripts, including a common toolset

# Bootstrapping environment
SCRIPTDIR="$( cd "$( dirname "$${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Environment variables
export pis_project_id=${PIS_PROJECT_ID}
export pis_gcp_zone=${PIS_GCP_ZONE}
export pis_is_partner_instance=${PIS_IS_PARTNER_INSTANCE}
export pis_data_release_skeleton_path_output_root=${PIS_DATA_RELEASE_SKELETON_PATH_OUTPUT_ROOT}
export pis_data_release_skeleton_path_input_root=${PIS_DATA_RELEASE_SKELETON_PATH_INPUT_ROOT}
export pis_data_release_skeleton_path_metadata_root=${PIS_DATA_RELEASE_SKELETON_PATH_METADATA_ROOT}
export pis_data_release_path_source_root=${PIS_DATA_RELEASE_PATH_SOURCE_ROOT}
export pis_data_release_path_input_root=${PIS_DATA_RELEASE_PATH_INPUT_ROOT}
export pis_flag_pipeline_scripts_ready=${PIS_FLAG_PIPELINE_SCRIPTS_READY}
export pis_gcp_path_pis_pipeline_session_logs=${PIS_GCP_PATH_PIS_PIPELINE_SESSION_LOGS}
export pis_path_pipeline_root=${PIS_PATH_PIPELINE_ROOT}
export pis_path_pipeline_scripts=${PIS_PATH_PIPELINE_SCRIPTS}
export pis_filename_pipeline_scripts_entry_point=${PIS_FILENAME_PIPELINE_SCRIPTS_ENTRY_POINT}

# Log folders
export pis_path_logs_pipeline="${PIS_PATH_PIPELINE_ROOT}/logs"
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