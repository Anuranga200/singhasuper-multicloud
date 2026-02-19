# Azure VM Scale Set Module for Multi-Cloud DR System
# Creates VM Scale Set with Docker-enabled instances

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# User-assigned managed identity for VMs
resource "azurerm_user_assigned_identity" "vmss" {
  name                = "${var.project_name}-${var.environment}-vmss-identity"
  resource_group_name = var.resource_group_name
  location            = var.azure_location

  tags = var.tags
}

# Grant Key Vault access to managed identity
resource "azurerm_key_vault_access_policy" "vmss" {
  key_vault_id = var.key_vault_id
  tenant_id    = var.tenant_id
  object_id    = azurerm_user_assigned_identity.vmss.principal_id

  secret_permissions = [
    "Get",
    "List"
  ]
}

# Cloud-init configuration
locals {
  cloud_init = <<-EOF
    #cloud-config
    package_update: true
    package_upgrade: true
    
    packages:
      - docker.io
      - docker-compose
      - jq
      - curl
    
    runcmd:
      - systemctl start docker
      - systemctl enable docker
      - usermod -aG docker azureuser
      
      # Install Azure CLI
      - curl -sL https://aka.ms/InstallAzureCLIDeb | bash
      
      # Create application directory
      - mkdir -p /opt/singha-loyalty
      - cd /opt/singha-loyalty
      
      # Login with managed identity
      - az login --identity
      
      # Retrieve secrets from Key Vault
      - |
        DB_HOST=$(az keyvault secret show --vault-name ${var.key_vault_name} --name db-host --query value -o tsv)
        DB_PORT=$(az keyvault secret show --vault-name ${var.key_vault_name} --name db-port --query value -o tsv)
        DB_NAME=$(az keyvault secret show --vault-name ${var.key_vault_name} --name db-name --query value -o tsv)
        DB_USER=$(az keyvault secret show --vault-name ${var.key_vault_name} --name db-username --query value -o tsv)
        DB_PASSWORD=$(az keyvault secret show --vault-name ${var.key_vault_name} --name db-password --query value -o tsv)
        JWT_SECRET=$(az keyvault secret show --vault-name ${var.key_vault_name} --name jwt-secret --query value -o tsv)
        JWT_REFRESH_SECRET=$(az keyvault secret show --vault-name ${var.key_vault_name} --name jwt-refresh-secret --query value -o tsv)
      
      # Create docker-compose.yml
      - |
        cat > /opt/singha-loyalty/docker-compose.yml <<'COMPOSE'
        version: '3.8'
        services:
          backend:
            image: ${var.docker_image}
            container_name: singha-backend
            restart: always
            ports:
              - "3000:3000"
            environment:
              NODE_ENV: production
              PORT: 3000
              DB_HOST: $DB_HOST
              DB_PORT: $DB_PORT
              DB_NAME: $DB_NAME
              DB_USER: $DB_USER
              DB_PASSWORD: $DB_PASSWORD
              JWT_SECRET: $JWT_SECRET
              JWT_REFRESH_SECRET: $JWT_REFRESH_SECRET
              CORS_ORIGIN: "*"
            healthcheck:
              test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
              interval: 30s
              timeout: 10s
              retries: 3
              start_period: 40s
            logging:
              driver: "json-file"
              options:
                max-size: "10m"
                max-file: "3"
          
          frontend:
            image: ${var.docker_image}
            container_name: singha-frontend
            restart: always
            ports:
              - "8080:8080"
            environment:
              VITE_API_BASE_URL: http://localhost:3000/api
            healthcheck:
              test: ["CMD", "curl", "-f", "http://localhost:8080"]
              interval: 30s
              timeout: 10s
              retries: 3
              start_period: 40s
            logging:
              driver: "json-file"
              options:
                max-size: "10m"
                max-file: "3"
        COMPOSE
      
      # Start containers
      - cd /opt/singha-loyalty && docker-compose up -d
      
      # Install Azure Monitor agent
      - wget https://aka.ms/azuremonitoragent-linux -O /tmp/azuremonitoragent.deb
      - dpkg -i /tmp/azuremonitoragent.deb
  EOF
}

# Linux VM Scale Set
resource "azurerm_linux_virtual_machine_scale_set" "main" {
  name                = "${var.project_name}-${var.environment}-vmss"
  resource_group_name = var.resource_group_name
  location            = var.azure_location
  sku                 = var.azure_vm_size
  instances           = var.instance_count
  admin_username      = "azureuser"

  admin_ssh_key {
    username   = "azureuser"
    public_key = var.ssh_public_key
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts-gen2"
    version   = "latest"
  }

  os_disk {
    storage_account_type = "Standard_LRS"
    caching              = "ReadWrite"
  }

  network_interface {
    name    = "primary"
    primary = true

    ip_configuration {
      name      = "internal"
      primary   = true
      subnet_id = var.private_app_subnet_id

      load_balancer_backend_address_pool_ids = [
        var.backend_pool_id
      ]
    }

    network_security_group_id = var.app_nsg_id
  }

  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.vmss.id
    ]
  }

  custom_data = base64encode(local.cloud_init)

  upgrade_mode = "Automatic"

  automatic_os_upgrade_policy {
    disable_automatic_rollback  = false
    enable_automatic_os_upgrade = true
  }

  health_probe_id = var.health_probe_id

  tags = var.tags
}

# Auto-scaling rules
resource "azurerm_monitor_autoscale_setting" "main" {
  name                = "${var.project_name}-${var.environment}-autoscale"
  resource_group_name = var.resource_group_name
  location            = var.azure_location
  target_resource_id  = azurerm_linux_virtual_machine_scale_set.main.id

  profile {
    name = "defaultProfile"

    capacity {
      default = var.instance_count
      minimum = var.min_instances
      maximum = var.max_instances
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 70
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT5M"
      }
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "LessThan"
        threshold          = 30
      }

      scale_action {
        direction = "Decrease"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT5M"
      }
    }
  }

  tags = var.tags
}

# Monitor alert for high CPU
resource "azurerm_monitor_metric_alert" "cpu" {
  name                = "${var.project_name}-${var.environment}-vmss-cpu"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_linux_virtual_machine_scale_set.main.id]
  description         = "Alert when VMSS CPU exceeds 80%"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachineScaleSets"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = var.action_group_id
  }

  tags = var.tags
}
