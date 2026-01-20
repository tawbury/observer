# Resource Group Module

resource "azurerm_resource_group" "this" {
  name     = var.name
  location = var.location
}

output "id" {
  value = azurerm_resource_group.this.id
}
