# Variables for Route 53 DNS and Health Checks Module

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (prod, staging, dev)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for CloudWatch resources"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "health_check_path" {
  description = "Path for health check endpoint"
  type        = string
  default     = "/health"
}

variable "health_check_interval" {
  description = "Health check interval in seconds (10 or 30)"
  type        = number
  default     = 30
  
  validation {
    condition     = contains([10, 30], var.health_check_interval)
    error_message = "Health check interval must be either 10 or 30 seconds."
  }
}

variable "failure_threshold" {
  description = "Number of consecutive failures before marking unhealthy"
  type        = number
  default     = 3
  
  validation {
    condition     = var.failure_threshold >= 1 && var.failure_threshold <= 10
    error_message = "Failure threshold must be between 1 and 10."
  }
}

variable "dns_ttl" {
  description = "DNS TTL in seconds for rapid failover"
  type        = number
  default     = 60
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 90
}

# AWS Primary Endpoint
variable "aws_endpoint" {
  description = "AWS ALB endpoint (FQDN)"
  type        = string
}

variable "aws_ip_address" {
  description = "AWS ALB IP address for DNS record"
  type        = string
}

# Azure Failover Endpoint
variable "azure_endpoint" {
  description = "Azure Load Balancer endpoint (FQDN)"
  type        = string
}

variable "azure_ip_address" {
  description = "Azure Load Balancer IP address for DNS record"
  type        = string
}

# GCP Failover Endpoint
variable "gcp_endpoint" {
  description = "GCP Load Balancer endpoint (FQDN)"
  type        = string
}

variable "gcp_ip_address" {
  description = "GCP Load Balancer IP address for DNS record"
  type        = string
}

# SNS Topic for Alerts
variable "sns_topic_arn" {
  description = "SNS topic ARN for health check alerts"
  type        = string
}
