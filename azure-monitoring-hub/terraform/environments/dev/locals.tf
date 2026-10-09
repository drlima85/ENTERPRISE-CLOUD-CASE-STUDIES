locals {
  project     = var.project
  environment = var.environment
  location    = var.location

  common_tags = merge(
    {
      Project     = "monhub"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}
