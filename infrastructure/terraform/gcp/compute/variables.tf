variable "project_name" { type = string }
variable "environment" { type = string }
variable "gcp_project" { type = string }
variable "gcp_region" { type = string }
variable "gcp_machine_type" { type = string; default = "e2-micro" }
variable "docker_image" { type = string }
variable "instance_count" { type = number; default = 2 }
variable "min_instances" { type = number; default = 2 }
variable "max_instances" { type = number; default = 4 }
variable "private_app_subnet_id" { type = string }
variable "secret_db_host" { type = string }
variable "secret_db_port" { type = string }
variable "secret_db_name" { type = string }
variable "secret_db_user" { type = string }
variable "secret_db_password" { type = string }
variable "secret_jwt" { type = string }
variable "secret_jwt_refresh" { type = string }
