# Route 53 DNS and Health Checks Module
# Provides global DNS routing with health-based failover

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Hosted Zone for the application
resource "aws_route53_zone" "main" {
  name    = var.domain_name
  comment = "Multi-cloud DR system hosted zone"

  tags = {
    Name        = "${var.project_name}-${var.environment}-zone"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Health Check for AWS Primary
resource "aws_route53_health_check" "aws_primary" {
  fqdn              = var.aws_endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_check_path
  failure_threshold = var.failure_threshold
  request_interval  = var.health_check_interval

  tags = {
    Name        = "${var.project_name}-${var.environment}-aws-health"
    Project     = var.project_name
    Environment = var.environment
    Cloud       = "AWS"
  }
}

# CloudWatch Alarm for AWS Health Check
resource "aws_cloudwatch_metric_alarm" "aws_health_alarm" {
  alarm_name          = "${var.project_name}-${var.environment}-aws-health-alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Alert when AWS primary endpoint is unhealthy"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    HealthCheckId = aws_route53_health_check.aws_primary.id
  }
}

# Health Check for Azure First Failover
resource "aws_route53_health_check" "azure_failover" {
  fqdn              = var.azure_endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_check_path
  failure_threshold = var.failure_threshold
  request_interval  = var.health_check_interval

  tags = {
    Name        = "${var.project_name}-${var.environment}-azure-health"
    Project     = var.project_name
    Environment = var.environment
    Cloud       = "Azure"
  }
}

# CloudWatch Alarm for Azure Health Check
resource "aws_cloudwatch_metric_alarm" "azure_health_alarm" {
  alarm_name          = "${var.project_name}-${var.environment}-azure-health-alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Alert when Azure failover endpoint is unhealthy"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    HealthCheckId = aws_route53_health_check.azure_failover.id
  }
}

# Health Check for GCP Second Failover
resource "aws_route53_health_check" "gcp_failover" {
  fqdn              = var.gcp_endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_check_path
  failure_threshold = var.failure_threshold
  request_interval  = var.health_check_interval

  tags = {
    Name        = "${var.project_name}-${var.environment}-gcp-health"
    Project     = var.project_name
    Environment = var.environment
    Cloud       = "GCP"
  }
}

# CloudWatch Alarm for GCP Health Check
resource "aws_cloudwatch_metric_alarm" "gcp_health_alarm" {
  alarm_name          = "${var.project_name}-${var.environment}-gcp-health-alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Alert when GCP failover endpoint is unhealthy"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    HealthCheckId = aws_route53_health_check.gcp_failover.id
  }
}

# Primary DNS Record (AWS) - Failover Primary
resource "aws_route53_record" "primary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  failover_routing_policy {
    type = "PRIMARY"
  }

  set_identifier  = "aws-primary"
  health_check_id = aws_route53_health_check.aws_primary.id
  ttl             = var.dns_ttl

  records = [var.aws_ip_address]
}

# Secondary DNS Record (Azure) - Failover Secondary
resource "aws_route53_record" "secondary_azure" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  failover_routing_policy {
    type = "SECONDARY"
  }

  set_identifier  = "azure-secondary"
  health_check_id = aws_route53_health_check.azure_failover.id
  ttl             = var.dns_ttl

  records = [var.azure_ip_address]
}

# Tertiary DNS Record (GCP) - Failover Tertiary
# Note: Route 53 only supports PRIMARY/SECONDARY, so we use weighted routing for GCP
resource "aws_route53_record" "tertiary_gcp" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "${var.environment}-gcp.${var.domain_name}"
  type    = "A"
  ttl     = var.dns_ttl

  weighted_routing_policy {
    weight = 100
  }

  set_identifier  = "gcp-tertiary"
  health_check_id = aws_route53_health_check.gcp_failover.id

  records = [var.gcp_ip_address]
}

# CNAME for www subdomain
resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  ttl     = var.dns_ttl
  records = [var.domain_name]
}

# Health Check Status Calculated Metric
resource "aws_route53_health_check" "calculated" {
  type                            = "CALCULATED"
  child_health_threshold          = 1
  child_healthchecks             = [
    aws_route53_health_check.aws_primary.id,
    aws_route53_health_check.azure_failover.id,
    aws_route53_health_check.gcp_failover.id
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-overall-health"
    Project     = var.project_name
    Environment = var.environment
  }
}

# CloudWatch Alarm for Overall System Health
resource "aws_cloudwatch_metric_alarm" "overall_health_alarm" {
  alarm_name          = "${var.project_name}-${var.environment}-overall-health-alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "CRITICAL: All cloud endpoints are unhealthy"
  alarm_actions       = [var.sns_topic_arn]
  treat_missing_data  = "breaching"

  dimensions = {
    HealthCheckId = aws_route53_health_check.calculated.id
  }
}

# CloudWatch Log Group for Query Logging
resource "aws_cloudwatch_log_group" "route53_queries" {
  name              = "/aws/route53/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-route53-logs"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Query Logging Configuration
resource "aws_route53_query_log" "main" {
  depends_on = [aws_cloudwatch_log_group.route53_queries]

  cloudwatch_log_group_arn = aws_cloudwatch_log_group.route53_queries.arn
  zone_id                  = aws_route53_zone.main.zone_id
}

# CloudWatch Dashboard for DNS Health
resource "aws_cloudwatch_dashboard" "dns_health" {
  dashboard_name = "${var.project_name}-${var.environment}-dns-health"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Route53", "HealthCheckStatus", { stat = "Average", label = "AWS Primary" }],
            [".", ".", { stat = "Average", label = "Azure Failover" }],
            [".", ".", { stat = "Average", label = "GCP Failover" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "Health Check Status"
          yAxis = {
            left = {
              min = 0
              max = 1
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Route53", "HealthCheckPercentageHealthy", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Overall Health Percentage"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      {
        type = "log"
        properties = {
          query   = "SOURCE '${aws_cloudwatch_log_group.route53_queries.name}' | fields @timestamp, query_name, query_type, rcode | sort @timestamp desc | limit 100"
          region  = var.aws_region
          title   = "Recent DNS Queries"
        }
      }
    ]
  })
}

# EventBridge Rule for Health Check State Changes
resource "aws_cloudwatch_event_rule" "health_check_state_change" {
  name        = "${var.project_name}-${var.environment}-health-state-change"
  description = "Capture Route 53 health check state changes"

  event_pattern = jsonencode({
    source      = ["aws.route53"]
    detail-type = ["Route 53 Health Check Status Change"]
    detail = {
      healthCheckId = [
        aws_route53_health_check.aws_primary.id,
        aws_route53_health_check.azure_failover.id,
        aws_route53_health_check.gcp_failover.id
      ]
    }
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-health-event-rule"
    Project     = var.project_name
    Environment = var.environment
  }
}

# EventBridge Target - SNS for Health Check State Changes
resource "aws_cloudwatch_event_target" "health_check_sns" {
  rule      = aws_cloudwatch_event_rule.health_check_state_change.name
  target_id = "SendToSNS"
  arn       = var.sns_topic_arn
}

# Output health check IDs for monitoring
output "health_check_ids" {
  value = {
    aws   = aws_route53_health_check.aws_primary.id
    azure = aws_route53_health_check.azure_failover.id
    gcp   = aws_route53_health_check.gcp_failover.id
  }
  description = "Health check IDs for all clouds"
}
