# GCP VPC Network Module for Multi-Cloud DR System
# Creates VPC with public and private subnets

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.project_name}-${var.environment}-vpc"
  auto_create_subnetworks = false
  project                 = var.gcp_project
}

# Public Subnet
resource "google_compute_subnetwork" "public" {
  name          = "${var.project_name}-${var.environment}-public-subnet"
  ip_cidr_range = cidrsubnet(var.vpc_cidr, 8, 0)
  region        = var.gcp_region
  network       = google_compute_network.main.id
  project       = var.gcp_project
}

# Private Subnet for Application
resource "google_compute_subnetwork" "private_app" {
  name          = "${var.project_name}-${var.environment}-private-app-subnet"
  ip_cidr_range = cidrsubnet(var.vpc_cidr, 8, 10)
  region        = var.gcp_region
  network       = google_compute_network.main.id
  project       = var.gcp_project
  
  private_ip_google_access = true
}

# Private Subnet for Database
resource "google_compute_subnetwork" "private_db" {
  name          = "${var.project_name}-${var.environment}-private-db-subnet"
  ip_cidr_range = cidrsubnet(var.vpc_cidr, 8, 20)
  region        = var.gcp_region
  network       = google_compute_network.main.id
  project       = var.gcp_project
  
  private_ip_google_access = true
}

# Cloud Router for NAT
resource "google_compute_router" "main" {
  name    = "${var.project_name}-${var.environment}-router"
  region  = var.gcp_region
  network = google_compute_network.main.id
  project = var.gcp_project
}

# Cloud NAT for outbound connectivity
resource "google_compute_router_nat" "main" {
  name                               = "${var.project_name}-${var.environment}-nat"
  router                             = google_compute_router.main.name
  region                             = google_compute_router.main.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  project                            = var.gcp_project
  
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall rule to allow health checks from Google Cloud Load Balancer
resource "google_compute_firewall" "allow_health_check" {
  name    = "${var.project_name}-${var.environment}-allow-health-check"
  network = google_compute_network.main.name
  project = var.gcp_project
  
  allow {
    protocol = "tcp"
    ports    = ["3000", "8080"]
  }
  
  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["app-server"]
}

# Firewall rule to allow internal communication
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.project_name}-${var.environment}-allow-internal"
  network = google_compute_network.main.name
  project = var.gcp_project
  
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "icmp"
  }
  
  source_ranges = [var.vpc_cidr]
}

# Firewall rule to allow SSH from IAP
resource "google_compute_firewall" "allow_iap_ssh" {
  name    = "${var.project_name}-${var.environment}-allow-iap-ssh"
  network = google_compute_network.main.name
  project = var.gcp_project
  
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["app-server"]
}

# Firewall rule for MySQL
resource "google_compute_firewall" "allow_mysql" {
  name    = "${var.project_name}-${var.environment}-allow-mysql"
  network = google_compute_network.main.name
  project = var.gcp_project
  
  allow {
    protocol = "tcp"
    ports    = ["3306"]
  }
  
  source_ranges = [
    google_compute_subnetwork.private_app.ip_cidr_range
  ]
  
  target_tags = ["mysql-server"]
}

# Private Service Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-${var.environment}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
  project       = var.gcp_project
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}
