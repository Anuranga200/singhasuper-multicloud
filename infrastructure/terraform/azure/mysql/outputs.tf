# Outputs for Azure MySQL Module

output "server_id" {
  description = "ID of the MySQL server"
  value       = azurerm_mysql_flexible_server.main.id
}

output "server_name" {
  description = "Name of the MySQL server"
  value       = azurerm_mysql_flexible_server.main.name
}

output "server_fqdn" {
  description = "FQDN of the MySQL server"
  value       = azurerm_mysql_flexible_server.main.fqdn
}

output "database_name" {
  description = "Name of the database"
  value       = azurerm_mysql_flexible_database.main.name
}

output "administrator_login" {
  description = "Administrator login name"
  value       = azurerm_mysql_flexible_server.main.administrator_login
  sensitive   = true
}
