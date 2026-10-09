# ==============================================================================
# Azure Virtual Network Gateway Compartilhado — US-05
# Azure Monitoring Hub (monhub) - Ambiente: dev
# Referência Arquitetural: ADR-001-vng-sku.md
# ==============================================================================

# Endereço IP Público dedicado ao Virtual Network Gateway
# Conforme ADR-001: SKU Standard, alocação Static e redundância zonal (Zone-Redundant)
resource "azurerm_public_ip" "vng" {
  name                = "pip-vng-monhub-dev-brs"
  resource_group_name = data.azurerm_resource_group.monhub.name
  location            = data.azurerm_resource_group.monhub.location
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = ["1", "2", "3"]

  tags = local.common_tags
}

# Azure Virtual Network Gateway compartilhado entre todos os clientes
# Tipo Vpn, roteamento RouteBased, SKU VpnGw1AZ (Generation 1, Zone-Redundant)
resource "azurerm_virtual_network_gateway" "monhub" {
  name                = "vng-monhub-dev-brs"
  resource_group_name = data.azurerm_resource_group.monhub.name
  location            = data.azurerm_resource_group.monhub.location

  type     = "Vpn"
  vpn_type = "RouteBased"

  active_active = false
  enable_bgp    = var.vng_enable_bgp
  sku           = var.vng_sku
  generation    = var.vng_generation

  ip_configuration {
    name                          = "vnetGatewayConfig"
    public_ip_address_id          = azurerm_public_ip.vng.id
    private_ip_address_allocation = "Dynamic"
    subnet_id                     = azurerm_subnet.gateway.id
  }

  tags = local.common_tags
}
