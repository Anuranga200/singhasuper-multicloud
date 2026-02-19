# GCP Compute Engine Module for Multi-Cloud DR System
# Creates Managed Instance Group with Docker-enabled instances

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Service Account for instances
resource "google_service_account" "instance" {
  account_id   = "${var.project_name}-${var.environment}-compute-sa"
  display_name = "Service Account for Compute Instances"
  project      = var.gcp_project
}

# IAM binding for Secret Manager access
resource "google_project_iam_member" "secret_accessor" {
  project = var.gcp_project
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.instance.email}"
}

# IAM binding for Cloud SQL Client
resource "google_project_iam_member" "cloudsql_client" {
  project = var.gcp_project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.instance.email}"
}

# IAM binding for Logging
resource "google_project_iam_member" "log_writer" {
  project = var.gcp_project
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.instance.email}"
}

# IAM binding for Monitoring
resource "google_project_iam_member" "monitoring_writer" {
  project = var.gcp_project
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.instance.email}"
}

# Startup script
locals {
  startup_script = <<-EOF
    #!/bin/bash
    set -e
    
    # Update system
    apt-get update
    apt-get install -y docker.io docker-compose jq curl
    
    # Start Docker
    systemctl start docker
    systemctl enable docker
    
    # Install gcloud SDK (if not present)
    if ! command -v gcloud &> /dev/null; then
      curl https://sdk.cloud.google.com | bash
      exec -l $SHELL
    fi
    
    # Create application directory
    mkdir -p /opt/singha-loyalty
    cd /opt/singha-loyalty
    
    # Retrieve secrets from Secret Manager
    DB_HOST=$(gcloud secrets versions access latest --secret="${var.secret_db_host}" --project=${var.gcp_project})
    DB_PORT=$(gcloud secrets versions access latest --secret="${var.secret_db_port}" --project=${var.gcp_project})
    DB_NAME=$(gcloud secrets versions access latest --secret="${var.secret_db_name}" --project=${var.gcp_project})
    DB_USER=$(gcloud secrets versions access latest --secret="${var.secret_db_user}" --project=${var.gcp_project})
    DB_PASSWORD=$(gcloud secrets versions access latest --secret="${var.secret_db_password}" --project=${var.gcp_project})
    JWT_SECRET=$(gcloud secrets versions access latest --secret="${var.secret_jwt}" --project=${var.gcp_project})
    JWT_REFRESH_SECRET=$(gcloud secrets versions access latest --secret="${var.secret_jwt_refresh}" --project=${var.gcp_project})
    
    # Create docker-compose.yml
    cat > docker-compose.yml <<'COMPOSE'
    version: '3.8'
    services:
      backend:
        image: ${var.docker_image}
        container_name: singha-backend
        restart: always
        ports:
          - "3000:3000"
        environment:
          NODE_ENV: production
          PORT: 3000
          DB_HOST: $DB_HOST
          DB_PORT: $DB_PORT
          DB_NAME: $DB_NAME
          DB_USER: $DB_USER
          DB_PASSWORD: $DB_PASSWORD
          JWT_SECRET: $JWT_SECRET
          JWT_REFRESH_SECRET: $JWT_REFRESH_SECRET
          CORS_ORIGIN: "*"
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
          interval: 30s
          timeout: 10s
          retries: 3
          start_period: 40s
      
      frontend:
        image: ${var.docker_image}
        container_name: singha-frontend
        restart: always
        ports:
          - "8080:8080"
        environment:
          VITE_API_BASE_URL: http://localhost:3000/api
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:8080"]
          interval: 30s
          timeout: 10s
          retries: 3
          start_period: 40s
    COMPOSE
    
    # Start containers
    docker-compose up -d
    
    # Install Cloud Ops Agent
    curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
    bash add-google-cloud-ops-agent-repo.sh --also-install
  EOF
}

# Instance Template
resource "google_compute_instance_template" "main" {
  name_prefix  = "${var.project_name}-${var.environment}-"
  machine_type = var.gcp_machine_type
  project      = var.gcp_project
  region       = var.gcp_region
  
  disk {
    source_image = "ubuntu-os-cloud/ubuntu-2004-lts"
    auto_delete  = true
    boot         = true
    disk_size_gb = 20
  }
  
  network_interface {
    subnetwork = var.private_app_subnet_id
  }
  
  metadata = {
    startup-script = local.startup_script
  }
  
  service_account {
    email  = google_service_account.instance.email
    scopes = ["cloud-platform"]
  }
  
  tags = ["app-server"]
  
  lifecycle {
    create_before_destroy = true
  }
}

# Health Check
resource "google_compute_health_check" "main" {
  name    = "${var.project_name}-${var.environment}-health-check"
  project = var.gcp_project
  
  http_health_check {
    port         = 3000
    request_path = "/health"
  }
  
  check_interval_sec  = 30
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3
}

# Instance Group Manager
resource "google_compute_region_instance_group_manager" "main" {
  name               = "${var.project_name}-${var.environment}-igm"
  base_instance_name = "${var.project_name}-${var.environment}"
  region             = var.gcp_region
  project            = var.gcp_project
  
  version {
    instance_template = google_compute_instance_template.main.id
  }
  
  target_size = var.instance_count
  
  named_port {
    name = "http"
    port = 3000
  }
  
  auto_healing_policies {
    health_check      = google_compute_health_check.main.id
    initial_delay_sec = 300
  }
}

# Autoscaler
resource "google_compute_region_autoscaler" "main" {
  name    = "${var.project_name}-${var.environment}-autoscaler"
  region  = var.gcp_region
  project = var.gcp_project
  target  = google_compute_region_instance_group_manager.main.id
  
  autoscaling_policy {
    max_replicas    = var.max_instances
    min_replicas    = var.min_instances
    cooldown_period = 300
    
    cpu_utilization {
      target = 0.7
    }
  }
}
