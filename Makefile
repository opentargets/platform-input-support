.EXPORT_ALL_VARIABLES:
PATH_SCRIPTS := scripts
OTOPS_PATH_CREDENTIALS := credentials
OTOPS_PATH_GCS_CREDENTIALS_GCP_FILE := "gs://open-targets-ops/credentials/pis-service_account.json"
OTOPS_PATH_GCS_CREDENTIALS_FILE := ${OTOPS_PATH_CREDENTIALS}/gcs_credentials.json
PIS_ACTIVE_PROFILE := .env
SESSION_ID := $(shell uuidgen | tr '''[:upper:]''' '''[:lower:]''' | cut -f5 -d'-')
PATH_PIS_SESSION := sessions/${SESSION_ID}
PATH_PIS_SESSION_CONTEXT := ${PATH_PIS_SESSION}/.env
config_dest ?= ${PATH_PIS_SESSION}

default: help

.PHONY: help
help: # Show help for each of the Makefile recipes.
	@grep -E '^[a-zA-Z0-9 -_]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

${OTOPS_PATH_GCS_CREDENTIALS_FILE}: # Target for fetching the GCP credintials. Alised by gcp_creditials
	@echo "[GOOGLE] Creating credentials file"
	@mkdir -p ${OTOPS_PATH_CREDENTIALS}
	@gsutil cp ${OTOPS_PATH_GCS_CREDENTIALS_GCP_FILE} ${OTOPS_PATH_GCS_CREDENTIALS_FILE}

.PHONY: gcp_credentials
gcp_credentials: ${OTOPS_PATH_GCS_CREDENTIALS_FILE} # Source GCP service account credentials

.PHONY: set_profile
set_profile: # Set an active configuration profile, e.g. "make set_profile profile='dev'" (see folder 'profiles')
	@echo "[PIS] Setting active profile '${profile}'"
	@ln -sf profiles/config.${profile} ${PIS_ACTIVE_PROFILE}

.PHONY: new_session
new_session: # Initialise the running context and start a new session
	@echo "[PIS] Setting running context"
	@echo ${SESSION_ID}
	@mkdir -p ${PATH_PIS_SESSION}
	@echo "[PIS] Creating context environment file (${PATH_PIS_SESSION_CONTEXT}) from active profile"
	@bash -c 'source ${PIS_ACTIVE_PROFILE} && ./${PATH_SCRIPTS}/init_context.sh' > ${PATH_PIS_SESSION_CONTEXT}

.PHONY: config_init
config_init: # Instantiate the PIS config. Optionally set the output directory with config_dest=<config output dir>
	@echo "[PIS] Instantiating PIS config"
	@mkdir -p ${config_dest}
	@echo "[PIS] Writing config to ==> ${config_dest}"
	$(eval include ${PIS_ACTIVE_PROFILE})
	@bash ./${PATH_SCRIPTS}/init_config.sh config.yaml ${config_dest}/config.yaml

.PHONY: launch_local
launch_local: gcp_credentials new_session config_init # Launch PIS locally
	@echo "[PIS] SESSION_ID: ${SESSION_ID}"
	@echo "[PIS] Launching PIS locally"
	@echo "Loading context: ${PATH_PIS_SESSION_CONTEXT}"
	$(eval include ${PIS_ACTIVE_PROFILE})
	@echo "[PIS] Preparing dirs"
	@mkdir -p ${OTOPS_PATH_PIS_OUTPUT_DIR}
	@mkdir -p ${OTOPS_PATH_PIS_LOGS_DIR}
	@echo "[PIS] Docker run with args: '${args}'"
	@bash ./${PATH_SCRIPTS}/run.sh ${args}
	@echo "[PIS] Uploading logs to GCS"
	@gsutil -m cp -r ${PATH_PIS_SESSION} ${OTOPS_PATH_GCS_PIS_SESSIONS}

.PHONY: clean_sessions_metadata
clean_sessions_metadata: # Clean all session metadata files
	@echo "[PIS] Removing all session metadata..."
	@rm -rv sessions