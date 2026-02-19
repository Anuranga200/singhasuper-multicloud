# Global Variables for Multi-Cloud DR System

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "singha-loyalty"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "docker_image" {
  description = "Docker image for the application"
  type        = string
  default     = "singha-loyalty-app:latest"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "singha_loyalty"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "jwt_refresh_secret" {
  description = "JWT refresh token secret key"
  type        = string
  sensitive   = true
}

# AWS specific variables
variable "aws_region" {
  description = "AWS region for primary deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "aws_db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

# Azure specific variables
variable "azure_location" {
  description = "Azure region for failover deployment"
  type        = string
  default     = "eastus"
}

variable "azure_vm_size" {
  description = "Azure VM size"
  type        = string
  default     = "Standard_B1s"
}

variable "azure_db_sku" {
  description = "Azure Database SKU"
  type        = string
  default     = "B_Gen5_1"
}

# GCP specific variables
variable "gcp_region" {
  description = "GCP region for failover deployment"
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "gcp_machine_type" {
  description = "GCP machine type"
  type        = string
  default     = "e2-micro"
}

variable "gcp_db_tier" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-f1-micro"
}

# Networking variables
variable "vpc_cidr_aws" {
  description = "CIDR block for AWS VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "vpc_cidr_azure" {
  description = "CIDR block for Azure VNet"
  type        = string
  default     = "10.1.0.0/16"
}

variable "vpc_cidr_gcp" {
  description = "CIDR block for GCP VPC"
  type        = string
  default     = "10.2.0.0/16"
}

# Monitoring variables
variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
}

variable "alert_phone" {
  description = "Phone number for SMS alerts (E.164 format)"
  type        = string
  default     = ""
}

# Cost monitoring variables
variable "monthly_budget_aws" {
  description = "Monthly budget for AWS in USD"
  type        = number
  default     = 100
}

variable "monthly_budget_azure" {
  description = "Monthly budget for Azure in USD"
  type        = number
  default     = 100
}

variable "monthly_budget_gcp" {
  description = "Monthly budget for GCP in USD"
  type        = number
  default     = 100
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Singha Loyalty DR"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}
