# GCP Cloud Load Balancing Module
terraform {
  required_providers {
    google = { source = "hashicorp/google"; version = "~> 5.0" }
  }
}

# Global IP Address
resource "google_compute_global_address" "main" {
  name    = "${var.project_name}-${var.environment}-lb-ip"
  project = var.gcp_project
}

# Backend Service
resource "google_compute_backend_service" "main" {
  name          = "${var.project_name}-${var.environment}-backend"
  project       = var.gcp_project
  health_checks = [var.health_check_id]
  port_name     = "http"
  protocol      = "HTTP"
  timeout_sec   = 30
  
  backend {
    group = var.instance_group_self_link
  }
}

# URL Map
resource "google_compute_url_map" "main" {
  name            = "${var.project_name}-${var.environment}-url-map"
  project         = var.gcp_project
  default_service = google_compute_backend_service.main.id
}

# HTTP Proxy
resource "google_compute_target_http_proxy" "main" {
  name    = "${var.project_name}-${var.environment}-http-proxy"
  project = var.gcp_project
  url_map = google_compute_url_map.main.id
}

# Forwarding Rule
resource "google_compute_global_forwarding_rule" "main" {
  name       = "${var.project_name}-${var.environment}-forwarding-rule"
  project    = var.gcp_project
  target     = google_compute_target_http_proxy.main.id
  port_range = "80"
  ip_address = google_compute_global_address.main.address
}
