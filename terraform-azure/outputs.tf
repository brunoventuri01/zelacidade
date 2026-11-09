output "application_url" {
  description = "URL HTTPS publica provisoria; o MVP oficial substituira a imagem nginx."
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "resource_group_name" {
  description = "Resource Group gerenciado pelo Terraform."
  value       = azurerm_resource_group.main.name
}

output "web_app_name" {
  description = "Nome usado pela futura pipeline de deploy."
  value       = azurerm_linux_web_app.main.name
}
