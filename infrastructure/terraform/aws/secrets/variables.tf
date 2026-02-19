# Variables for AWS Secrets Manager Module

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
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

variable "api_key" {
  description = "API key for external services"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cors_origin" {
  description = "CORS origin for the application"
  type        = string
  default     = "*"
}

variable "db_secret_arn" {
  description = "ARN of the database credentials secret"
  type        = string
}

variable "alert_email" {
  description = "Email address for rotation alerts"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
