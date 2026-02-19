# GCP Cloud SQL MySQL Module for Multi-Cloud DR System
# Creates Cloud SQL MySQL instance as read replica from AWS RDS

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Random suffix for unique instance name
resource "random_id" "db_name_suffix" {
  byte_length = 4
}

# Cloud SQL MySQL Instance
resource "google_sql_database_instance" "main" {
  name             = "${var.project_name}-${var.environment}-mysql-${random_id.db_name_suffix.hex}"
  database_version = "MYSQL_8_0"
  region           = var.gcp_region
  project          = var.gcp_project
  
  settings {
    tier              = var.gcp_db_tier
    availability_type = "REGIONAL"  # High availability
    disk_size         = 20
    disk_type         = "PD_SSD"
    disk_autoresize   = true
    
    backup_configuration {
      enabled            = true
      start_time         = "03:00"
      binary_log_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_self_link
      require_ssl     = true
    }
    
    database_flags {
      name  = "max_connections"
      value = "100"
    }
    
    database_flags {
      name  = "binlog_format"
      value = "ROW"
    }
    
    database_flags {
      name  = "binlog_expire_logs_seconds"
      value = "604800"
    }
    
    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
    }
    
    maintenance_window {
      day          = 1  # Monday
      hour         = 4
      update_track = "stable"
    }
  }
  
  deletion_protection = true
  
  depends_on = [var.private_vpc_connection]
}

# Database
resource "google_sql_database" "main" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
  project  = var.gcp_project
  charset  = "utf8mb4"
  collation = "utf8mb4_unicode_ci"
}

# Database User
resource "google_sql_user" "main" {
  name     = var.db_username
  instance = google_sql_database_instance.main.name
  password = var.db_password
  project  = var.gcp_project
}

# Monitoring Alert for CPU
resource "google_monitoring_alert_policy" "cpu" {
  display_name = "${var.project_name}-${var.environment}-cloudsql-cpu"
  project      = var.gcp_project
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud SQL CPU utilization"
    
    condition_threshold {
      filter          = "resource.type = \"cloudsql_database\" AND resource.labels.database_id = \"${var.gcp_project}:${google_sql_database_instance.main.name}\" AND metric.type = \"cloudsql.googleapis.com/database/cpu/utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = var.notification_channels
}

# Monitoring Alert for Memory
resource "google_monitoring_alert_policy" "memory" {
  display_name = "${var.project_name}-${var.environment}-cloudsql-memory"
  project      = var.gcp_project
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud SQL memory utilization"
    
    condition_threshold {
      filter          = "resource.type = \"cloudsql_database\" AND resource.labels.database_id = \"${var.gcp_project}:${google_sql_database_instance.main.name}\" AND metric.type = \"cloudsql.googleapis.com/database/memory/utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = var.notification_channels
}

# Monitoring Alert for Disk
resource "google_monitoring_alert_policy" "disk" {
  display_name = "${var.project_name}-${var.environment}-cloudsql-disk"
  project      = var.gcp_project
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud SQL disk utilization"
    
    condition_threshold {
      filter          = "resource.type = \"cloudsql_database\" AND resource.labels.database_id = \"${var.gcp_project}:${google_sql_database_instance.main.name}\" AND metric.type = \"cloudsql.googleapis.com/database/disk/utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = var.notification_channels
}
