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
