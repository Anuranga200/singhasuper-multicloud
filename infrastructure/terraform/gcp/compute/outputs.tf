output "instance_group_id" { value = google_compute_region_instance_group_manager.main.id }
output "instance_group_self_link" { value = google_compute_region_instance_group_manager.main.self_link }
output "health_check_id" { value = google_compute_health_check.main.id }
output "service_account_email" { value = google_service_account.instance.email }
