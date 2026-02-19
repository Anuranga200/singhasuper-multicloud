# Azure Database for MySQL Module for Multi-Cloud DR System
# Creates MySQL Flexible Server as read replica from AWS RDS

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# MySQL Flexible Server
resource "azurerm_mysql_flexible_server" "main" {
  name                = "${var.project_name}-${var.environment}-mysql"
  resource_group_name = var.resource_group_name
  location            = var.azure_location

  administrator_login    = var.db_username
  administrator_password = var.db_password

  sku_name = var.azure_db_sku
  version  = "8.0.21"

  storage {
    size_gb           = 20
    auto_grow_enabled = true
  }

  backup_retention_days        = 30
  geo_redundant_backup_enabled = true

  high_availability {
    mode = "ZoneRedundant"
  }

  delegated_subnet_id = var.private_db_subnet_id

  tags = var.tags
}

# MySQL Database
resource "azurerm_mysql_flexible_database" "main" {
  name                = var.db_name
  resource_group_name = var.resource_group_name
  server_name         = azurerm_mysql_flexible_server.main.name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
}

# Firewall rule to allow Azure services
resource "azurerm_mysql_flexible_server_firewall_rule" "azure_services" {
  name                = "AllowAzureServices"
  resource_group_name = var.resource_group_name
  server_name         = azurerm_mysql_flexible_server.main.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
}

# Configuration for replication
resource "azurerm_mysql_flexible_server_configuration" "binlog_format" {
  name                = "binlog_format"
  resource_group_name = var.resource_group_name
  server_name         = azurerm_mysql_flexible_server.main.name
  value               = "ROW"
}

resource "azurerm_mysql_flexible_server_configuration" "binlog_expire_logs_seconds" {
  name                = "binlog_expire_logs_seconds"
  resource_group_name = var.resource_group_name
  server_name         = azurerm_mysql_flexible_server.main.name
  value               = "604800"
}

# Monitor for CPU utilization
resource "azurerm_monitor_metric_alert" "cpu" {
  name                = "${var.project_name}-${var.environment}-mysql-cpu"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_mysql_flexible_server.main.id]
  description         = "Alert when CPU exceeds 80%"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.DBforMySQL/flexibleServers"
    metric_name      = "cpu_percent"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = var.action_group_id
  }

  tags = var.tags
}

# Monitor for storage utilization
resource "azurerm_monitor_metric_alert" "storage" {
  name                = "${var.project_name}-${var.environment}-mysql-storage"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_mysql_flexible_server.main.id]
  description         = "Alert when storage exceeds 80%"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.DBforMySQL/flexibleServers"
    metric_name      = "storage_percent"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = var.action_group_id
  }

  tags = var.tags
}

# Monitor for connection count
resource "azurerm_monitor_metric_alert" "connections" {
  name                = "${var.project_name}-${var.environment}-mysql-connections"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_mysql_flexible_server.main.id]
  description         = "Alert when active connections exceed 80"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.DBforMySQL/flexibleServers"
    metric_name      = "active_connections"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = var.action_group_id
  }

  tags = var.tags
}

# Diagnostic settings for logging
resource "azurerm_monitor_diagnostic_setting" "mysql" {
  name                       = "${var.project_name}-${var.environment}-mysql-diagnostics"
  target_resource_id         = azurerm_mysql_flexible_server.main.id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category = "MySqlSlowLogs"
  }

  enabled_log {
    category = "MySqlAuditLogs"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}
