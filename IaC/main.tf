# main.tf

provider "azurerm" {
  features {}
  subscription_id = "8fd0bb7e-9db8-44e7-a19c-bfb0e514ffa0"
}

data "azurerm_client_config" "current" {}

resource "random_integer" "suffix" {
  min = 10000
  max = 99999
}

# 1. Resource Group
resource "azurerm_resource_group" "main" {
  name     = "smartcart-rg"
  location = "Central US"
}

# 2. Azure Container Registry
resource "azurerm_container_registry" "acr" {
  name                = "smartcartregistry${random_integer.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
}

# 3. PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "db" {
  name                   = "smartcart-db"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  administrator_login    = "smartadmin"
  administrator_password = var.db_password
  sku_name               = "B_Standard_B1ms"
  version                = "13"
  storage_mb             = 32768
  zone = null
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name         = "allow-azure"
  server_id    = azurerm_postgresql_flexible_server.db.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# 4. App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "smartcart-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1"
}

# 5. App Service for Docker
resource "azurerm_linux_web_app" "smartcart" {
  name                = "smartcart-application"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      docker_image_name        = "${azurerm_container_registry.acr.login_server}/smartcart"
      docker_registry_url      = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
    }
  }

  app_settings = {
    "DATABASE_URL"    = azurerm_postgresql_flexible_server.db.fqdn
    "OPENAI_API_KEY"  = var.openai_api_key
  }
}

# 6. Azure Key Vault
resource "azurerm_key_vault" "vault" {
  name                        = "smartcart-vault-${random_integer.suffix.result}"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  purge_protection_enabled    = true
}

resource "azurerm_key_vault_secret" "openai_key" {
  name         = "OpenAIApiKey"
  value        = var.openai_api_key
  key_vault_id = azurerm_key_vault.vault.id

  depends_on = [
    azurerm_key_vault_access_policy.main
  ]
}

resource "azurerm_key_vault_access_policy" "main" {
  key_vault_id = azurerm_key_vault.vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "Set", "List", "Delete"]
}

# variables.tf

variable "openai_api_key" {
  type        = string
  description = "The OpenAI API key"
  sensitive   = true
}

variable "db_password" {
  type        = string
  description = "Admin password for PostgreSQL"
  sensitive   = true
}

# outputs.tf

output "app_service_url" {
  value       = azurerm_linux_web_app.smartcart.default_hostname
  description = "SmartCart application URL"
}

output "acr_login_server" {
  value       = azurerm_container_registry.acr.login_server
  description = "Azure Container Registry login server"
}

output "key_vault_uri" {
  value       = azurerm_key_vault.vault.vault_uri
  description = "URI for accessing Key Vault"
}
