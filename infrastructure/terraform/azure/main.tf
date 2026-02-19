# Main Azure Infrastructure Deployment
terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm"; version = "~> 3.0" }
  }
}

provider "azurerm" {
  features {}
}

module "vnet" {
  source = "./vnet"
  project_name   = var.project_name
  environment    = var.environment
  azure_location = var.azure_location
  vnet_cidr      = var.vpc_cidr_azure
  tags           = var.tags
}

module "keyvault" {
  source = "./keyvault"
  project_name        = var.project_name
  environment         = var.environment
  resource_group_name = module.vnet.resource_group_name
  azure_location      = var.azure_location
  db_host             = module.mysql.server_fqdn
  db_password         = var.db_password
  jwt_secret          = var.jwt_secret
  jwt_refresh_secret  = var.jwt_refresh_secret
  tags                = var.tags
}

module "mysql" {
  source = "./mysql"
  project_name           = var.project_name
  environment            = var.environment
  resource_group_name    = module.vnet.resource_group_name
  azure_location         = var.azure_location
  db_name                = var.db_name
  db_username            = var.db_username
  db_password            = var.db_password
  private_db_subnet_id   = module.vnet.private_db_subnet_id
  action_group_id        = ""  # Add monitoring module
  log_analytics_workspace_id = ""  # Add monitoring module
  tags                   = var.tags
}

module "lb" {
  source = "./lb"
  project_name        = var.project_name
  environment         = var.environment
  resource_group_name = module.vnet.resource_group_name
  azure_location      = var.azure_location
  tags                = var.tags
}

module "vmss" {
  source = "./vmss"
  project_name          = var.project_name
  environment           = var.environment
  resource_group_name   = module.vnet.resource_group_name
  azure_location        = var.azure_location
  docker_image          = var.docker_image
  private_app_subnet_id = module.vnet.private_app_subnet_id
  app_nsg_id            = module.vnet.app_nsg_id
  backend_pool_id       = module.lb.backend_pool_id
  health_probe_id       = module.lb.health_probe_id
  key_vault_id          = module.keyvault.key_vault_id
  key_vault_name        = module.keyvault.key_vault_name
  tenant_id             = module.keyvault.tenant_id
  ssh_public_key        = var.ssh_public_key
  action_group_id       = ""  # Add monitoring module
  tags                  = var.tags
}
