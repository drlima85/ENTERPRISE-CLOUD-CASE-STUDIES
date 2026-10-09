# ==============================================================================
# Camada Base de Networking — US-04
# Azure Monitoring Hub (monhub) - Ambiente: dev
# ==============================================================================

# Virtual Network principal
# Faixas reservadas para expansão futura (não provisionadas nesta etapa):
# - 10.240.2.0/24
# - 10.240.4.0/22
# - 10.240.8.0/21
resource "azurerm_virtual_network" "monhub" {
  name                = "vnet-monhub-dev-brs"
  resource_group_name = data.azurerm_resource_group.monhub.name
  location            = data.azurerm_resource_group.monhub.location
  address_space       = ["10.240.0.0/20"]

  tags = local.common_tags
}

# Subnet obrigatória para o Azure Virtual Network Gateway (sem NSG)
resource "azurerm_subnet" "gateway" {
  name                 = "GatewaySubnet"
  resource_group_name  = data.azurerm_resource_group.monhub.name
  virtual_network_name = azurerm_virtual_network.monhub.name
  address_prefixes     = ["10.240.0.0/26"]
}

# Subnet dedicada aos collectors de monitoramento
resource "azurerm_subnet" "collectors" {
  name                 = "snet-collectors-dev-brs"
  resource_group_name  = data.azurerm_resource_group.monhub.name
  virtual_network_name = azurerm_virtual_network.monhub.name
  address_prefixes     = ["10.240.1.0/24"]
}

# Network Security Group dedicado à subnet de collectors
resource "azurerm_network_security_group" "collectors" {
  name                = "nsg-collectors-dev-brs"
  resource_group_name = data.azurerm_resource_group.monhub.name
  location            = data.azurerm_resource_group.monhub.location

  tags = local.common_tags
}

# Associação exclusiva do NSG à subnet de collectors (GatewaySubnet não possui NSG)
resource "azurerm_subnet_network_security_group_association" "collectors" {
  subnet_id                 = azurerm_subnet.collectors.id
  network_security_group_id = azurerm_network_security_group.collectors.id
}
