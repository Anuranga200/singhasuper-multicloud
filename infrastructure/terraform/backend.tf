# Terraform Backend Configuration
# This file configures remote state storage for Terraform
# 
# IMPORTANT: Update the bucket name and region before using
# Each cloud provider should use a separate state file

terraform {
  # Minimum Terraform version
  required_version = ">= 1.5.0"

  # Backend configuration for AWS S3
  # Uncomment and configure for production use
  # backend "s3" {
  #   bucket         = "singha-loyalty-terraform-state"
  #   key            = "multi-cloud-dr/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }

  # Alternative: Azure Blob Storage backend
  # backend "azurerm" {
  #   resource_group_name  = "terraform-state-rg"
  #   storage_account_name = "singhaloyaltyterraform"
  #   container_name       = "tfstate"
  #   key                  = "multi-cloud-dr.tfstate"
  # }

  # Alternative: GCS backend
  # backend "gcs" {
  #   bucket = "singha-loyalty-terraform-state"
  #   prefix = "multi-cloud-dr"
  # }
}

# Provider version constraints
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}
