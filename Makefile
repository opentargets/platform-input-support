.EXPORT_ALL_VARIABLES:
PATH_SCRIPTS := launcher/scripts/pipeline
OTOPS_PATH_CREDENTIALS := credentials
OTOPS_PATH_GCS_CREDENTIALS_GCP_FILE := "gs://open-targets-ops/credentials/pis-service_account.json"
OTOPS_PATH_GCS_CREDENTIALS_FILE := ${OTOPS_PATH_CREDENTIALS}/gcs_credentials.json
PIS_ACTIVE_PROFILE := .env
SESSION_ID := $(shell uuidgen | tr '''[:upper:]''' '''[:lower:]''' | cut -f5 -d'-')
PATH_PIS_SESSION := sessions/${SESSION_ID}
PATH_PIS_SESSION_CONTEXT := ${PATH_PIS_SESSION}/.env
config_dest ?= ${PATH_PIS_SESSION}
OTOPS_PATH_PIS_CONFIG := ${config_dest}/config.yaml
OTOPS_PIS_RUN_ARGS := "${args}"
OTOPS_PATH_GCS_PIS_SESSION_LOGS := gs://open-targets-ops/logs/platform-pis/
current_session_id=$(shell cat .sessionid)

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
	@echo "${SESSION_ID}" > .sessionid
	@mkdir -p ${PATH_PIS_SESSION}
	@echo "[PIS] Creating context environment file (${PATH_PIS_SESSION_CONTEXT}) from active profile"
	@bash -c 'set -o allexport && \
		source ${PIS_ACTIVE_PROFILE} && \
		set +o allexport && \
		./${PATH_SCRIPTS}/init_context.sh' > ${PATH_PIS_SESSION_CONTEXT}

.PHONY: switch_session
switch_session: # Switch to another existing session e.g. "make switch_session session='abcdef1234'" (see folder 'sessions')
	@echo "[PIS] Switching to session: '${session}'"
	@echo "${session}" > .sessionid

.PHONY: config_init
config_init: # Instantiate the PIS config. Optionally set the output directory with config_dest=<config output dir>
	@echo "[PIS] Instantiating PIS config"
	@mkdir -p ${config_dest}
	@echo "[PIS] Writing config to ==> ${OTOPS_PATH_PIS_CONFIG}"
	$(eval include ${PIS_ACTIVE_PROFILE})
	@bash ./${PATH_SCRIPTS}/init_config.sh config.yaml ${OTOPS_PATH_PIS_CONFIG}

.PHONY: launch_local
launch_local: gcp_credentials new_session config_init # Launch PIS locally
	@echo "[PIS] Session ID: ${current_session_id}"
	@echo "[PIS] Launching PIS locally"
	@echo "Loading context: ${PATH_PIS_SESSION_CONTEXT}"
	$(eval include ${PIS_ACTIVE_PROFILE})
	@echo "[PIS] Preparing dirs"
	@mkdir -p ${OTOPS_PATH_PIS_OUTPUT_DIR}
	@mkdir -p ${OTOPS_PATH_PIS_LOGS_DIR}
	@echo "[PIS] Docker run with args: '${OTOPS_PIS_RUN_ARGS}'"
	@bash ./${PATH_SCRIPTS}/run.sh
	@echo "[PIS] Uploading config/context to GCS: ${OTOPS_PATH_GCS_PIS_SESSION_CONFIGS}/${current_session_id}"
	@gsutil -m rsync -r ${PATH_PIS_SESSION} ${OTOPS_PATH_GCS_PIS_SESSION_CONFIGS}/${current_session_id}/
	@echo "[PIS] Logs will be uploaded to GCS when pipeline has completed: ${OTOPS_PATH_GCS_PIS_SESSION_LOGS}${current_session_id}"

.PHONY: launch_local_nogcp
launch_local_nogcp: gcp_credentials new_session config_init # Launch PIS locally without uploading to GCS
	@echo "[PIS] Session ID: ${current_session_id}"
	@echo "[PIS] Launching PIS locally"
	@echo "Loading context: ${PATH_PIS_SESSION_CONTEXT}"
	$(eval include ${PIS_ACTIVE_PROFILE})
	@echo "[PIS] Preparing dirs"
	@mkdir -p ${OTOPS_PATH_PIS_OUTPUT_DIR}
	@mkdir -p ${OTOPS_PATH_PIS_LOGS_DIR}
	@echo "[PIS] Docker run with args: '${OTOPS_PIS_RUN_ARGS}'"
	@bash ./${PATH_SCRIPTS}/run.sh --nogcp

.PHONY: launch_remote
launch_remote: gcp_credentials new_session config_init # Launch PIS remotely
	@echo "[PIS] Session ID: ${current_session_id}"
	@echo "Loading context: ${PATH_PIS_SESSION_CONTEXT}"
	$(eval include ${PIS_ACTIVE_PROFILE})
	@echo "[PIS] Launching PIS remotely"
	@echo "[TERRAFORM] Using Terraform Workspace ID '${current_session_id}'" && \
		terraform -chdir=launcher init && \
		terraform -chdir=launcher workspace new ${current_session_id} && \
		terraform -chdir=launcher apply -auto-approve
	@echo "[PIS] Uploading config/context to GCS: ${OTOPS_PATH_GCS_PIS_SESSION_CONFIGS}/${current_session_id}"
	@gsutil -m rsync -r ${PATH_PIS_SESSION} ${OTOPS_PATH_GCS_PIS_SESSION_CONFIGS}/${current_session_id}/
	@echo "[PIS] Logs will be uploaded to GCS when pipeline has completed: ${OTOPS_PATH_GCS_PIS_SESSION_LOGS}"

.PHONY: clean_all_sessions_metadata
clean_all_sessions_metadata: # Clean all session metadata files
	@echo "[PIS] Removing all session metadata..."
	@rm -rv sessions

.PHONY: clean_session_metadata
clean_session_metadata: # Clean metadata files for the current session
	@echo "[PIS] Removing metadata for session: ${current_session_id}"
	@rm -rv sessions/${current_session_id}/

.PHONY: clean_infrastructure
clean_infrastructure: # Clean the infrastructure for the session
	@cd launcher ; \
		terraform init && \
		echo "[TERRAFORM] Cleaning up Workspace ID '$${current_session_id}'" \
		terraform workspace select ${current_session_id} && \
		terraform destroy

.PHONY: clean_all_infrastructure
clean_all_infrastructure: ## Clean all the infrastructures used for run PIS remotely
	@cd launcher ; \
	terraform init && \
	terraform workspace select default && \
	for ws in $$( terraform workspace list | cut -f2 -d'*' ) ; do \
		if [ $$ws != 'default' ] ; then \
			echo "[CLEAN] Terraform workspace '$$ws'"; \
			terraform workspace select $$ws ; \
			terraform destroy -auto-approve ; \
			terraform workspace select default ; \
			terraform workspace delete $$ws ; \
		fi \
	done
