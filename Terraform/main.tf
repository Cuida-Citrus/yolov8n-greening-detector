terraform {
  required_version = ">= 1.0.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# 1. Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "rg-greening-dev"
  location = "East US"
}

# 2. Storage Account
resource "azurerm_storage_account" "sa" {
  name                     = "stgreeningdev"           # deve ser único globalmente, sem hífens
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  allow_blob_public_access = true
}

# 2.1 Container de input (acesso privado)
resource "azurerm_storage_container" "input" {
  name                  = "input-container"
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = "private"
}

# 2.2 Container predict-source (acesso público nível blob)
resource "azurerm_storage_container" "predict" {
  name                  = "predict-source"
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = "blob"
}

# 3. Cosmos DB Account
resource "azurerm_cosmosdb_account" "cosmos" {
  name                = "cosmosgreeningdev"       # único globalmente
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"        # SQL API
  consistency_policy {
    consistency_level = "Session"
  }
  geo_location {
    location          = azurerm_resource_group.rg.location
    failover_priority = 0
  }
}

# 3.1 Banco de dados SQL
resource "azurerm_cosmosdb_sql_database" "db" {
  name                = "GreeningDetection"
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.cosmos.name
}

# 3.2 Container SQL
resource "azurerm_cosmosdb_sql_container" "predicoes" {
  name                = "Predicoes"
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.cosmos.name
  database_name       = azurerm_cosmosdb_sql_database.db.name
  partition_key_path  = "/id"
  throughput          = 400
}

# 4. Outputs: endpoint, chave e connection string
output "COSMOS_ENDPOINT" {
  value = azurerm_cosmosdb_account.cosmos.endpoint
}

output "COSMOS_KEY" {
  value     = azurerm_cosmosdb_account.cosmos.primary_master_key
  sensitive = true
}

output "STORAGE_CONNECTION_STRING" {
  value     = azurerm_storage_account.sa.primary_connection_string
  sensitive = true
}
