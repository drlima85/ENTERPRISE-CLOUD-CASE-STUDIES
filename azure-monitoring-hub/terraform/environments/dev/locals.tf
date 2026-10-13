locals {
  project     = var.project
  environment = var.environment
  location    = var.location

  # ==============================================================================
  # Fonte Única de Verdade (Single Source of Truth - SSOT) dos Clientes — US-06
  # Consumida tanto pelo validador Python quanto pelos módulos Terraform (US-07/US-08)
  # ==============================================================================
  customers_file_path = "${path.module}/../../../data/customers.json"
  customers_data      = jsondecode(file(local.customers_file_path)).customers

  common_tags = merge(
    {
      Project     = "monhub"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}
