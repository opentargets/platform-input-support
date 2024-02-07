// This file defines the VM used for running PIS

resource "random_string" "pisvm" {
  length  = 8
  lower   = true
  upper   = false
  special = false
  keepers = {
    vm_pis_boot_disk_size = var.vm_pis_boot_disk_size
    // Take into account the machine type as well
    machine_type = var.vm_pis_machine_type
    // Be aware of launch script changes
    launch_script_hash = md5(file("${path.module}/scripts/pisvm/startup.sh"))
  }
}

// Key pair for SSH access
resource "tls_private_key" "pisvm" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

// PIS VM instance definition
resource "google_compute_instance" "pisvm" {
  project                   = var.project_id
  name                      = "${local.pisvm_name_prefix}-${random_string.pisvm.result}"
  machine_type              = var.vm_pis_machine_type
  zone                      = var.gcp_default_zone
  allow_stopping_for_update = true
  // TODO This should be set to false
  can_ip_forward = true

  scheduling {
    automatic_restart           = !var.vm_pis_machine_spot
    on_host_maintenance         = var.vm_pis_machine_spot ? "TERMINATE" : "MIGRATE"
    preemptible                 = var.vm_pis_machine_spot
    provisioning_model          = var.vm_pis_machine_spot ? "SPOT" : "STANDARD"
    instance_termination_action = var.vm_pis_machine_spot ? "STOP" : null
  }

  boot_disk {
    initialize_params {
      image = var.vm_pis_boot_image
      type  = "pd-ssd"
      size  = var.vm_pis_boot_disk_size
    }
  }

  // WARNING - Does this machine need a public IP. No cloud routing for eu-dev.
  network_interface {
    network = "default"
    access_config {
      network_tier = "PREMIUM"
    }
  }

  metadata = {
    startup-script = templatefile(
      "${path.module}/scripts/pisvm/startup.sh",
      {
        PROJECT_ID                            = var.project_id,
        GC_ZONE                               = var.gcp_default_zone,
        PIS_USER_NAME                         = local.pisvm_remote_user_name
        FLAG_PIPELINE_SCRIPTS_READY           = local.flag_pipeline_scripts_ready,
        PATH_PIPELINE_SCRIPTS                 = local.path_pipeline_scripts,
        FILENAME_PIPELINE_SCRIPTS_ENTRY_POINT = local.filename_pipeline_scripts_entry_point,
        CONTEXT_PATH                          = local.path_context
        PIS_VM_HOME                           = local.pisvm_remote_path_home
      }
    )
    ssh-keys               = "${local.pisvm_remote_user_name}:${tls_private_key.pisvm.public_key_openssh}"
    google-logging-enabled = true
  }

  service_account {
    email  = "pis-service-account@${var.project_id}.iam.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }

  // We add the lifecyle configuration
  lifecycle {
    create_before_destroy = true
  }

  // Provision the postproduction scripts
  connection {
    type        = "ssh"
    host        = self.network_interface[0].access_config[0].nat_ip
    user        = local.pisvm_remote_user_name
    private_key = tls_private_key.pisvm.private_key_pem
  }
  // Create remote folders
  provisioner "remote-exec" {
    inline = [
      "mkdir -p ${local.path_pipeline_scripts} credentials sessions/${terraform.workspace} output logs",
    ]
  }
  // Common configuration
  provisioner "file" {
    content = templatefile("${local.path_source_pipeline_scripts}/config.sh", {
      PIS_FLAG_PIPELINE_SCRIPTS_READY                  = local.flag_pipeline_scripts_ready,
      PIS_GCP_PATH_PIS_PIPELINE_SESSION_LOGS           = local.gcp_path_pis_pipeline_session_logs,
      PIS_PATH_PIPELINE_ROOT                           = local.path_pipeline_root,
      PIS_PATH_PIPELINE_SCRIPTS                        = local.path_pipeline_scripts,
      PIS_FILENAME_PIPELINE_SCRIPTS_ENTRY_POINT        = local.filename_pipeline_scripts_entry_point,
      }
    )
    destination = "${local.path_pipeline_scripts}/config.sh"
  }
  // Launch PIS file
  provisioner "file" {
    source      = "${local.path_source_pipeline_scripts}/run.sh"
    destination = "${local.path_pipeline_scripts}/run.sh"
  } 
  // Credentials file
  provisioner "file" {
    source      = "${local.path_source_credentials}/gcs_credentials.json"
    destination = "credentials/gcs_credentials.json"
  }
  // PIS config and context
  provisioner "file" {
    source      = "${local.path_source_session}/"
    destination = "${local.path_context}"
  }
  // Adjust scripts permissions
  provisioner "remote-exec" {
    inline = [
      "chmod 755 ${local.path_pipeline_scripts}/run.sh",
    ]
  }
  // Provision the operations extensions for BASH
  provisioner "file" {
    source      = "${local.path_source_pipeline_scripts}/ops.bashrc"
    destination = "${local.path_pipeline_scripts}/ops.bashrc"
  }
  // Tell BASH to load the operations extensions
  provisioner "remote-exec" {
    inline = [
      "echo \"source ${local.path_pipeline_scripts}/ops.bashrc\" >> ~/.bashrc",
    ]
  }
  // Tell BASH to export the context environment variables
  provisioner "remote-exec" {
    inline = [
      "echo \"source ${local.path_context}/.env\" >> ~/.bashrc",
    ]
  }
  // Set the 'ready' flag for the pipeline pipeline to start
  provisioner "remote-exec" {
    inline = [
      "touch ${local.flag_pipeline_scripts_ready}",
    ]
  }
}
