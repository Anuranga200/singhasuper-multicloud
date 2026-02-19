# Main AWS Infrastructure Deployment
# This file orchestrates all AWS modules for the primary cloud deployment

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# VPC and Networking
module "vpc" {
  source = "./vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr_aws
  tags         = var.tags
}

# RDS MySQL Database
module "rds" {
  source = "./rds"

  project_name          = var.project_name
  environment           = var.environment
  db_instance_class     = var.aws_db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  private_subnet_ids    = module.vpc.private_subnet_ids
  rds_security_group_id = module.vpc.rds_security_group_id
  alarm_actions         = [module.sns.topic_arn]
  tags                  = var.tags

  depends_on = [module.vpc]
}

# Secrets Manager
module "secrets" {
  source = "./secrets"

  project_name       = var.project_name
  environment        = var.environment
  jwt_secret         = var.jwt_secret
  jwt_refresh_secret = var.jwt_refresh_secret
  api_key            = var.api_key
  cors_origin        = var.cors_origin
  db_secret_arn      = module.rds.secret_arn
  alert_email        = var.alert_email
  tags               = var.tags

  depends_on = [module.rds]
}

# Application Load Balancer
module "alb" {
  source = "./alb"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.vpc.alb_security_group_id
  certificate_arn       = var.certificate_arn
  access_logs_bucket    = var.access_logs_bucket
  alarm_actions         = [module.sns.topic_arn]
  tags                  = var.tags

  depends_on = [module.vpc]
}

# EC2 Auto Scaling Group
module "ec2" {
  source = "./ec2"

  project_name          = var.project_name
  environment           = var.environment
  aws_region            = var.aws_region
  instance_type         = var.aws_instance_type
  docker_image          = var.docker_image
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.vpc.app_security_group_id
  target_group_arns     = module.alb.target_group_arns
  db_secret_name        = module.rds.secret_name
  app_secret_name       = module.secrets.app_secrets_name
  secrets_arns          = [module.rds.secret_arn, module.secrets.app_secrets_arn]
  min_instances         = var.min_instances
  max_instances         = var.max_instances
  desired_instances     = var.desired_instances
  alarm_actions         = [module.sns.topic_arn]
  tags                  = var.tags

  depends_on = [module.alb, module.rds, module.secrets]
}

# SNS Topic for Alerts
module "sns" {
  source = "./sns"

  project_name = var.project_name
  environment  = var.environment
  alert_email  = var.alert_email
  alert_phone  = var.alert_phone
  tags         = var.tags
}

# Route 53 Health Check
resource "aws_route53_health_check" "primary" {
  fqdn              = module.alb.alb_dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-health-check"
    }
  )
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average" }],
            [".", "RequestCount", { stat = "Sum" }],
            [".", "HTTPCode_Target_5XX_Count", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ALB Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { stat = "Average" }],
            [".", "DatabaseConnections", { stat = "Average" }],
            [".", "FreeStorageSpace", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "RDS Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", { stat = "Average" }],
            [".", "NetworkIn", { stat = "Sum" }],
            [".", "NetworkOut", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "EC2 Metrics"
        }
      }
    ]
  })
}
