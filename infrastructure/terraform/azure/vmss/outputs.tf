# Outputs for Azure VMSS Module

output "vmss_id" {
  description = "ID of the VM Scale Set"
  value       = azurerm_linux_virtual_machine_scale_set.main.id
}

output "vmss_name" {
  description = "Name of the VM Scale Set"
  value       = azurerm_linux_virtual_machine_scale_set.main.name
}

output "identity_principal_id" {
  description = "Principal ID of the managed identity"
  value       = azurerm_user_assigned_identity.vmss.principal_id
}

output "identity_id" {
  description = "ID of the managed identity"
  value       = azurerm_user_assigned_identity.vmss.id
}
