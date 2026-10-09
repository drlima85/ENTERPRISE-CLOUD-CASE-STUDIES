terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-monhub-tfstate-brs"
    storage_account_name = "stmonhubtfstatedevbrs"
    container_name       = "tfstate"
    key                  = "monhub-dev.tfstate"
    use_azuread_auth     = true
  }
}
