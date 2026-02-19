output "lb_ip_address" { value = google_compute_global_address.main.address }
output "backend_service_id" { value = google_compute_backend_service.main.id }
output "url_map_id" { value = google_compute_url_map.main.id }
