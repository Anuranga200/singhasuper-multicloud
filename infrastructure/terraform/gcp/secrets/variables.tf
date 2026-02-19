variable "project_name" { type = string }
variable "environment" { type = string }
variable "gcp_project" { type = string }
variable "db_host" { type = string }
variable "db_name" { type = string }
variable "db_username" { type = string; sensitive = true }
variable "db_password" { type = string; sensitive = true }
variable "jwt_secret" { type = string; sensitive = true }
variable "jwt_refresh_secret" { type = string; sensitive = true }
