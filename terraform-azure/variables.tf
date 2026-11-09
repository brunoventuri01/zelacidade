variable "subscription_id" {
  description = "ID da assinatura Azure; fornecido fora do repositorio."
  type        = string
  sensitive   = true
}

variable "location" {
  description = "Regiao permitida pela politica da assinatura para o App Service."
  type        = string
  default     = "eastus2"
}

