variable "resource_group_name" {
  description = "Nome do Resource Group existente para o ambiente de desenvolvimento do projeto."
  type        = string
  default     = "rg-monhub-dev-brs"
}

variable "location" {
  description = "Região padrão do Azure para os recursos do projeto."
  type        = string
  default     = "brazilsouth"
}

variable "environment" {
  description = "Identificador do ambiente de implantação."
  type        = string
  default     = "dev"
}

variable "project" {
  description = "Identificador do projeto."
  type        = string
  default     = "monhub"
}

variable "tags" {
  description = "Tags adicionais para os recursos."
  type        = map(string)
  default     = {}
}

# ------------------------------------------------------------------------------
# Variáveis — Virtual Network Gateway (US-05 / ADR-001)
# ------------------------------------------------------------------------------

variable "vng_sku" {
  description = "SKU do Azure Virtual Network Gateway. Conforme ADR-001, o valor padrão é VpnGw1AZ (Zone-Redundant)."
  type        = string
  default     = "VpnGw1AZ"
}

variable "vng_generation" {
  description = "Geração de arquitetura do Azure Virtual Network Gateway."
  type        = string
  default     = "Generation1"
}

variable "vng_enable_bgp" {
  description = "Indica se o suporte a Border Gateway Protocol (BGP) deve ser habilitado no gateway."
  type        = bool
  default     = false
}
