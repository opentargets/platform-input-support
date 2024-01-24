locals {
  // --- PIS VM Configuration --- //
  // Logging to the remote host, details
  pisvm_remote_user_name = "otops"
  pisvm_remote_path_home = "/home/${local.pisvm_remote_user_name}"
  // IAM role to be used to create the VM
  pisvm_roles = ["roles/compute.admin", "roles/logging.viewer", "roles/compute.instanceAdmin", "roles/storage.objectViewer", "roles/storage.admin"]
  // VM name
  pisvm_name_prefix = "${var.resources_prefix}-pisvm"
  // Postproduction source provisioning root path
  path_source_pipeline_scripts                = "${path.module}/scripts/pipeline"
  path_source_credentials                     = "${path.cwd}/credentials"
  path_source_session                         = "${path.cwd}/sessions/${terraform.workspace}"
  
  // --- Open Targets Data Release Skeleton --- //
  data_release_skeleton_path_output_root      = "output"
  data_release_skeleton_path_input_root       = "input"
  data_release_skeleton_path_etl_root         = "${local.data_release_skeleton_path_output_root}/etl"
  data_release_skeleton_path_etl_json_root    = "${local.data_release_skeleton_path_etl_root}/json"
  data_release_skeleton_path_etl_parquet_root = "${local.data_release_skeleton_path_etl_root}/parquet"
  data_release_skeleton_path_metadata_root     = "${local.data_release_skeleton_path_output_root}/metadata"

  // --- Open Targets Data Release --- //
  data_release_path_source_root = "gs://${var.data_location_source}"
  data_release_path_etl_json    = "${local.data_release_path_source_root}/${local.data_release_skeleton_path_etl_json_root}"
  data_release_path_etl_parquet = "${local.data_release_path_source_root}/${local.data_release_skeleton_path_etl_parquet_root}"
  data_release_path_input_root  = "${local.data_release_path_source_root}/${local.data_release_skeleton_path_input_root}"

  // --- PIS VM data load process configuration --- //
  // Base path to the pipeline pipeline scripts
  path_pipeline_root                               = "${local.pisvm_remote_path_home}/pis"
  path_pipeline_scripts                            = "${local.path_pipeline_root}/scripts"
  path_context                                     = "sessions/${terraform.workspace}"
  // Name of the pipeline pipeline scripts entry point
  filename_pipeline_scripts_entry_point = "${local.path_pipeline_scripts}/run.sh"
  // Flag to signal that the pipeline pipeline scripts are ready to run
  flag_pipeline_scripts_ready = "/${local.path_pipeline_root}/ready"
  // PIS pipeline session logs upload path
  gcp_path_pis_pipeline_session_logs = "${var.pis_logs_path_root}/${terraform.workspace}"
  // --- [END] PIS VM data load process configuration [END] --- //

  // --- Labels Configuration --- //
  base_labels = {
    "team"    = "open-targets"
    "subteam" = "backend"
    "product" = "platform"
    "tool"    = "pis"
  }
}