# Outputs for Azure VNet Module

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_id" {
  description = "ID of the resource group"
  value       = azurerm_resource_group.main.id
}

output "vnet_id" {
  description = "ID of the Virtual Network"
  value       = azurerm_virtual_network.main.id
}

output "vnet_name" {
  description = "Name of the Virtual Network"
  value       = azurerm_virtual_network.main.name
}

output "public_subnet_id" {
  description = "ID of public subnet"
  value       = azurerm_subnet.public.id
}

output "private_app_subnet_id" {
  description = "ID of private app subnet"
  value       = azurerm_subnet.private_app.id
}

output "private_db_subnet_id" {
  description = "ID of private database subnet"
  value       = azurerm_subnet.private_db.id
}

output "lb_nsg_id" {
  description = "ID of load balancer NSG"
  value       = azurerm_network_security_group.lb.id
}

output "app_nsg_id" {
  description = "ID of application NSG"
  value       = azurerm_network_security_group.app.id
}

output "db_nsg_id" {
  description = "ID of database NSG"
  value       = azurerm_network_security_group.db.id
}

output "nat_gateway_id" {
  description = "ID of NAT Gateway"
  value       = azurerm_nat_gateway.main.id
}
