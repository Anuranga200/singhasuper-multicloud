output "secret_db_host" { value = google_secret_manager_secret.db_host.secret_id }
output "secret_db_port" { value = google_secret_manager_secret.db_port.secret_id }
output "secret_db_name" { value = google_secret_manager_secret.db_name.secret_id }
output "secret_db_user" { value = google_secret_manager_secret.db_user.secret_id }
output "secret_db_password" { value = google_secret_manager_secret.db_password.secret_id }
output "secret_jwt" { value = google_secret_manager_secret.jwt.secret_id }
output "secret_jwt_refresh" { value = google_secret_manager_secret.jwt_refresh.secret_id }
