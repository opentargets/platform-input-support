// Open Targets Platform Infrastructure

// --- Provider Configuration --- //
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.55.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 4.55.0"
    }
  }
}

provider "google" {
  region  = var.gcp_default_region
  project = var.project_id
  zone    = var.gcp_default_zone
}


provider "google-beta" {
  project = var.project_id
  region  = var.gcp_default_region
  zone    = var.gcp_default_zone
}
