# Azure Load Balancer Module
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

resource "azurerm_public_ip" "lb" {
  name                = "${var.project_name}-${var.environment}-lb-pip"
  location            = var.azure_location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_lb" "main" {
  name                = "${var.project_name}-${var.environment}-lb"
  location            = var.azure_location
  resource_group_name = var.resource_group_name
  sku                 = "Standard"
  
  frontend_ip_configuration {
    name                 = "PublicIPAddress"
    public_ip_address_id = azurerm_public_ip.lb.id
  }
  tags = var.tags
}

resource "azurerm_lb_backend_address_pool" "main" {
  loadbalancer_id = azurerm_lb.main.id
  name            = "BackendPool"
}

resource "azurerm_lb_probe" "backend" {
  loadbalancer_id = azurerm_lb.main.id
  name            = "backend-health"
  protocol        = "Http"
  port            = 3000
  request_path    = "/health"
  interval_in_seconds = 30
  number_of_probes    = 3
}

resource "azurerm_lb_rule" "backend" {
  loadbalancer_id                = azurerm_lb.main.id
  name                           = "backend-rule"
  protocol                       = "Tcp"
  frontend_port                  = 443
  backend_port                   = 3000
  frontend_ip_configuration_name = "PublicIPAddress"
  backend_address_pool_ids       = [azurerm_lb_backend_address_pool.main.id]
  probe_id                       = azurerm_lb_probe.backend.id
}
