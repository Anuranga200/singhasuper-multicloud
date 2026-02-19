variable "project_name" { type = string }
variable "environment" { type = string }
variable "resource_group_name" { type = string }
variable "azure_location" { type = string }
variable "tags" { type = map(string); default = {} }
