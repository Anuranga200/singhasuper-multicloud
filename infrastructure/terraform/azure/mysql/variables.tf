# Variables for Azure MySQL Module

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "azure_location" {
  description = "Azure region"
  type        = string
}

variable "azure_db_sku" {
  description = "Azure Database SKU"
  type        = string
  default     = "B_Standard_B1s"
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database administrator username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database administrator password"
  type        = string
  sensitive   = true
}

variable "private_db_subnet_id" {
  description = "ID of private database subnet"
  type        = string
}

variable "action_group_id" {
  description = "ID of Azure Monitor action group for alerts"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "ID of Log Analytics workspace"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
