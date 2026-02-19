# Variables for AWS EC2 Module

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "docker_image" {
  description = "Docker image for the application"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for instances"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group ID for application instances"
  type        = string
}

variable "target_group_arns" {
  description = "List of target group ARNs for load balancer"
  type        = list(string)
}

variable "db_secret_name" {
  description = "Name of Secrets Manager secret containing DB credentials"
  type        = string
}

variable "app_secret_name" {
  description = "Name of Secrets Manager secret containing app secrets"
  type        = string
}

variable "secrets_arns" {
  description = "List of Secrets Manager ARNs to grant access to"
  type        = list(string)
}

variable "min_instances" {
  description = "Minimum number of instances in ASG"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of instances in ASG"
  type        = number
  default     = 4
}

variable "desired_instances" {
  description = "Desired number of instances in ASG"
  type        = number
  default     = 2
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
