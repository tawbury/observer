terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0"
    }
  }
  required_version = ">= 1.0.0"
}

provider "azurerm" {
  features {}
  subscription_id = "632e6f30-269e-42d2-96a5-9c3618bd358e"
  tenant_id       = "cbd7850b-7a48-4769-80f5-3b08ab27243f"
}
