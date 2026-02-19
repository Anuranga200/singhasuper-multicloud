# Variables for AWS Main Deployment

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "singha-loyalty"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr_aws" {
  description = "CIDR block for AWS VPC"
  type        = string
  default     = "10.0.0.0/16"
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

variable "docker_image" {
  description = "Docker image for the application"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "singha_loyalty"
}

variable "db_username" {
  description = "Database master username"
  type        = string
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

variable "certificate_arn" {
  description = "ARN of ACM certificate for HTTPS"
  type        = string
  default     = ""
}

variable "access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}

variable "min_instances" {
  description = "Minimum number of EC2 instances"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of EC2 instances"
  type        = number
  default     = 4
}

variable "desired_instances" {
  description = "Desired number of EC2 instances"
  type        = number
  default     = 2
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
}

variable "alert_phone" {
  description = "Phone number for SMS alerts"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Singha Loyalty DR"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}
