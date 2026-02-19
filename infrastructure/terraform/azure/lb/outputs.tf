output "lb_id" { value = azurerm_lb.main.id }
output "lb_public_ip" { value = azurerm_public_ip.lb.ip_address }
output "backend_pool_id" { value = azurerm_lb_backend_address_pool.main.id }
output "health_probe_id" { value = azurerm_lb_probe.backend.id }
