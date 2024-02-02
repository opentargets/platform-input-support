terraform {
  backend "gcs" {
    bucket = "open-targets-ops"
    prefix = "terraform/platform-pis"
  }
}