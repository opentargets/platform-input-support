#!/bin/bash
# Startup script for PIS VM Instance

# Environment variables
flag_startup_completed="/tmp/pisvm_startup_complete"

# Logging helper function
function log() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $@"
}

# This function updates the system and installs the required packages
function install_packages() {
  log "Updating system"
  sudo apt-get update
  log "Installing required packages"
  sudo apt-get install -y ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce
  log "Adding PIS user '${PIS_USER_NAME}' to docker group"
  sudo usermod -aG docker ${PIS_USER_NAME}
  newgrp docker
}

# Script completion hook to flag that 'startup script' has already been run
function startup_complete() {
  log "Startup script completed"
  touch $${flag_startup_completed}
}

# Environment summary function
function env_summary() {
  log "Environment summary:"
  log "  PROJECT_ID: ${PROJECT_ID}"
  log "  FLAG_PIPELINE_SCRIPTS_READY: ${FLAG_PIPELINE_SCRIPTS_READY}"
  log "  PATH_PIPELINE_SCRIPTS: ${PATH_PIPELINE_SCRIPTS}"
  log "  FILENAME_PIPELINE_SCRIPTS_ENTRY_POINT: ${FILENAME_PIPELINE_SCRIPTS_ENTRY_POINT}"
}

# Set trap to run 'startup_complete' function on exit
trap startup_complete EXIT

# Check if startup script has already been run
if [[ -f $${flag_startup_completed} ]]; then
  log "Startup script already completed, skipping"
  exit 0
fi

# Main Script
log "===> [BOOTSTRAP] PIS support VM <==="
env_summary
install_packages
# Wait until the "ready" flag for pipeline scripts is set, timeout after 20 minutes
log "Waiting for pipeline scripts to be ready, timeout after 20 minutes"
timeout 1200 bash -c "until [[ -f ${FLAG_PIPELINE_SCRIPTS_READY} ]]; do sleep 1; done"
# Launch the pipeline scripts
cd ${PIS_VM_HOME}
log "Setting context from: ${CONTEXT_PATH}/.env"
source ${CONTEXT_PATH}/.env
log "Launching pipeline script: ${FILENAME_PIPELINE_SCRIPTS_ENTRY_POINT}"
${FILENAME_PIPELINE_SCRIPTS_ENTRY_POINT}
log "Pipeline scripts completed"
# Shutting down this pipeline machine
log "[--- Shutting down this pipeline machine ---]"
poweroff