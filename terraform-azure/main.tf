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

  # A pipeline troca a tag da imagem a cada commit. O Terraform gerencia a
  # infraestrutura, mas nao deve desfazer o deploy realizado pelo CI/CD.
  lifecycle {
    ignore_changes = [
      app_settings["WEBSITES_ENABLE_APP_SERVICE_STORAGE"],
      site_config[0].application_stack[0].docker_image_name,
      site_config[0].application_stack[0].docker_registry_url,
    ]
  }
}

# Alerta operacional: indica respostas 5xx acima do limite em uma janela curta.
resource "azurerm_monitor_metric_alert" "http_5xx" {
  name                = "alert-zelacidade-http5xx"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.main.id]
  description         = "Alerta quando o ZelaCidade acumula mais de 5 respostas HTTP 5xx em 5 minutos."
  severity            = 1
  frequency           = "PT1M"
  window_size         = "PT5M"
  auto_mitigate       = true
  enabled             = true
  tags                = local.tags

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Http5xx"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 5
  }
}

# Evidencia controlada: permite comprovar o disparo do Azure Monitor sem
# provocar falha no aplicativo. O limite baixo considera uma janela de 5 min.
resource "azurerm_monitor_metric_alert" "traffic_evidence" {
  name                = "alert-zelacidade-traffic-evidence"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.main.id]
  description         = "Alerta controlado para evidenciar o funcionamento do monitoramento durante a GS."
  severity            = 4
  frequency           = "PT1M"
  window_size         = "PT5M"
  auto_mitigate       = true
  enabled             = true
  tags                = local.tags

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Requests"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 5
  }
}
