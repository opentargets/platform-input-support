// --- PIS configuration --- //

variable "resources_prefix" {
  description = "Prefix to use for all resources deployed in the cloud, default 'pis-unset'"
  type        = string
  default     = "pis-unset"
}
variable "data_location_source" {
  description = "Source location for the data release being processed, default 'open-targets-pre-data-releases/devpis'"
  type        = string
  default     = "open-targets-pre-data-releases/devpis"
}
variable "project_id" {
  description = "GCP project where the resources will be deployed, default 'open-targets-eu-dev'"
  type        = string
  default     = "open-targets-eu-dev"
}
variable "gcp_default_region" {
  description = "GCP region where the resources will be deployed, default 'europe-west1'"
  type        = string
  default     = "europe-west1"
}
variable "gcp_default_zone" {
  description = "GCP zone where the resources will be deployed, default 'europe-west1-d'"
  type        = string
  default     = "europe-west1-d"
}

// --- pis VM Configuration --- //
variable "vm_pis_boot_image" {
  description = "Boot image configuration for pis VM, default 'Debian 11'"
  type        = string
  default     = "debian-11"
}

variable "vm_pis_boot_disk_size" {
  description = "pis VM boot disk size, default '512GB'"
  type        = string
  default     = 512
}

variable "vm_pis_machine_type" {
  description = "Machine type for pis vm, default 'e2-standard-4'"
  type        = string
  default     = "e2-standard-8"
}

variable "vm_pis_machine_spot" {
  description = "Should SPOT provisioning model be used for pis VM?, default 'false'"
  type        = bool
  default     = false
}

variable "pis_logs_path_root" {
  description = "GCS root path where pis pipeline logs will be uploaded for the different pis sessions, default 'gs://open-targets-ops/logs/platform-pis'"
  type        = string
  default     = "gs://open-targets-ops/logs/platform-pis"
}
