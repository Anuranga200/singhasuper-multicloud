# Main GCP Infrastructure Deployment
terraform {
  required_providers {
    google = { source = "hashicorp/google"; version = "~> 5.0" }
  }
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

module "vpc" {
  source       = "./vpc"
  project_name = var.project_name
  environment  = var.environment
  gcp_project  = var.gcp_project
  gcp_region   = var.gcp_region
  vpc_cidr     = var.vpc_cidr_gcp
}

module "secrets" {
  source             = "./secrets"
  project_name       = var.project_name
  environment        = var.environment
  gcp_project        = var.gcp_project
  db_host            = module.cloudsql.private_ip_address
  db_name            = var.db_name
  db_username        = var.db_username
  db_password        = var.db_password
  jwt_secret         = var.jwt_secret
  jwt_refresh_secret = var.jwt_refresh_secret
}

module "cloudsql" {
  source                 = "./cloudsql"
  project_name           = var.project_name
  environment            = var.environment
  gcp_project            = var.gcp_project
  gcp_region             = var.gcp_region
  db_name                = var.db_name
  db_username            = var.db_username
  db_password            = var.db_password
  network_self_link      = module.vpc.network_self_link
  private_vpc_connection = module.vpc.private_vpc_connection
}

module "compute" {
  source                = "./compute"
  project_name          = var.project_name
  environment           = var.environment
  gcp_project           = var.gcp_project
  gcp_region            = var.gcp_region
  docker_image          = var.docker_image
  private_app_subnet_id = module.vpc.private_app_subnet_id
  secret_db_host        = module.secrets.secret_db_host
  secret_db_port        = module.secrets.secret_db_port
  secret_db_name        = module.secrets.secret_db_name
  secret_db_user        = module.secrets.secret_db_user
  secret_db_password    = module.secrets.secret_db_password
  secret_jwt            = module.secrets.secret_jwt
  secret_jwt_refresh    = module.secrets.secret_jwt_refresh
}

module "lb" {
  source                   = "./lb"
  project_name             = var.project_name
  environment              = var.environment
  gcp_project              = var.gcp_project
  health_check_id          = module.compute.health_check_id
  instance_group_self_link = module.compute.instance_group_self_link
}
