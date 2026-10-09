output "resource_group_name" {
  description = "Nome do Resource Group existente consultado."
  value       = data.azurerm_resource_group.monhub.name
}

output "resource_group_id" {
  description = "ID do Resource Group existente consultado."
  value       = data.azurerm_resource_group.monhub.id
}

output "resource_group_location" {
  description = "Localização do Resource Group existente consultado."
  value       = data.azurerm_resource_group.monhub.location
}

# ------------------------------------------------------------------------------
# Outputs — Networking (US-04)
# ------------------------------------------------------------------------------

output "vnet_id" {
  description = "ID da Virtual Network principal do projeto."
  value       = azurerm_virtual_network.monhub.id
}

output "vnet_name" {
  description = "Nome da Virtual Network principal do projeto."
  value       = azurerm_virtual_network.monhub.name
}

output "gateway_subnet_id" {
  description = "ID da GatewaySubnet dedicada ao Virtual Network Gateway."
  value       = azurerm_subnet.gateway.id
}

output "collectors_subnet_id" {
  description = "ID da subnet dedicada aos collectors de monitoramento."
  value       = azurerm_subnet.collectors.id
}

output "collectors_nsg_id" {
  description = "ID do Network Security Group associado à subnet de collectors."
  value       = azurerm_network_security_group.collectors.id
}
