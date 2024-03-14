// POS VM name
output "pisvm" {
  value = {
    name = google_compute_instance.pisvm.name
    zone = google_compute_instance.pisvm.zone
    username = local.pisvm_remote_user_name
  }
  description = "PIS VM information"
}