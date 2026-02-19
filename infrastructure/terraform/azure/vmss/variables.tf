# Variables for Azure VMSS Module

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

variable "azure_vm_size" {
  description = "Azure VM size"
  type        = string
  default     = "Standard_B1s"
}

variable "docker_image" {
  description = "Docker image for the application"
  type        = string
}

variable "instance_count" {
  description = "Number of VM instances"
  type        = number
  default     = 2
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 4
}

variable "private_app_subnet_id" {
  description = "ID of private app subnet"
  type        = string
}

variable "app_nsg_id" {
  description = "ID of application NSG"
  type        = string
}

variable "backend_pool_id" {
  description = "ID of load balancer backend pool"
  type        = string
}

variable "health_probe_id" {
  description = "ID of load balancer health probe"
  type        = string
}

variable "key_vault_id" {
  description = "ID of Key Vault"
  type        = string
}

variable "key_vault_name" {
  description = "Name of Key Vault"
  type        = string
}

variable "tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
}

variable "action_group_id" {
  description = "ID of Azure Monitor action group"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
