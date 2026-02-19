# GCP Secret Manager Module
terraform {
  required_providers {
    google = { source = "hashicorp/google"; version = "~> 5.0" }
  }
}

resource "google_secret_manager_secret" "db_host" {
  secret_id = "${var.project_name}-${var.environment}-db-host"
  project   = var.gcp_project
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "db_host" {
  secret      = google_secret_manager_secret.db_host.id
  secret_data = var.db_host
}

resource "google_secret_manager_secret" "db_port" {
  secret_id = "${var.project_name}-${var.environment}-db-port"
  project   = var.gcp_project
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "db_port" {
  secret      = google_secret_manager_secret.db_port.id
  secret_data = "3306"
}

resource "google_secret_manager_secret" "db_name" {
  secret_id = "${var.project_name}-${var.environment}-db-name"
  project   = var.gcp_project
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "db_name" {
  secret      = google_secret_manager_secret.db_name.id
  secret_data = var.db_name
}

resource "google_secret_manager_secret" "db_user" {
  secret_id = "${var.project_name}-${var.environment}-db-user"
  project   = var.gcp_project
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "db_user" {
  secret      = google_secret_manager_secret.db_user.id
  secret_data = var.db_username
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.project_name}-${var.environment}-db-password"
  project   = var.gcp_project
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "jwt" {
  secret_id = "${var.project_name}-${var.environment}-jwt-secret"
  project   = var.gcp_project
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "jwt" {
  secret      = google_secret_manager_secret.jwt.id
  secret_data = var.jwt_secret
}

resource "google_secret_manager_secret" "jwt_refresh" {
  secret_id = "${var.project_name}-${var.environment}-jwt-refresh-secret"
  project   = var.gcp_project
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "jwt_refresh" {
  secret      = google_secret_manager_secret.jwt_refresh.id
  secret_data = var.jwt_refresh_secret
}
