locals {
  prefix = "zelacidade-gs-99431"
  tags = {
    project     = "ZelaCidade"
    environment = "production"
    managed_by  = "Terraform"
    course      = "FIAP-GS-2026.2"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.prefix}"
  location = "eastus"
  tags     = local.tags
}

resource "azurerm_service_plan" "main" {
  name                = "asp-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "F1"
  tags                = local.tags
}

resource "azurerm_linux_web_app" "main" {
  name                                           = "app-${local.prefix}"
  resource_group_name                            = azurerm_resource_group.main.name
  location                                       = azurerm_service_plan.main.location
  service_plan_id                                = azurerm_service_plan.main.id
  https_only                                     = true
  ftp_publish_basic_authentication_enabled       = false
  webdeploy_publish_basic_authentication_enabled = false
  tags                                           = local.tags

  site_config {
    always_on = false

    application_stack {
      docker_image_name   = "nginx:1.27-alpine"
      docker_registry_url = "https://index.docker.io"
    }
  }

  app_settings = {
    WEBSITES_PORT = "80"
  }
}
