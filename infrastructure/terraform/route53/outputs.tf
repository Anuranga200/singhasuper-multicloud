# Outputs for Route 53 DNS and Health Checks Module

output "zone_id" {
  description = "Route 53 hosted zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "zone_name_servers" {
  description = "Name servers for the hosted zone"
  value       = aws_route53_zone.main.name_servers
}

output "domain_name" {
  description = "Domain name for the application"
  value       = var.domain_name
}

output "health_check_ids" {
  description = "Health check IDs for all clouds"
  value = {
    aws   = aws_route53_health_check.aws_primary.id
    azure = aws_route53_health_check.azure_failover.id
    gcp   = aws_route53_health_check.gcp_failover.id
  }
}

output "health_check_calculated_id" {
  description = "Calculated health check ID for overall system health"
  value       = aws_route53_health_check.calculated.id
}

output "primary_record_name" {
  description = "Primary DNS record name"
  value       = aws_route53_record.primary.name
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name for DNS queries"
  value       = aws_cloudwatch_log_group.route53_queries.name
}

output "cloudwatch_dashboard_name" {
  description = "CloudWatch dashboard name for DNS health monitoring"
  value       = aws_cloudwatch_dashboard.dns_health.dashboard_name
}

output "alarm_arns" {
  description = "CloudWatch alarm ARNs for health checks"
  value = {
    aws_health     = aws_cloudwatch_metric_alarm.aws_health_alarm.arn
    azure_health   = aws_cloudwatch_metric_alarm.azure_health_alarm.arn
    gcp_health     = aws_cloudwatch_metric_alarm.gcp_health_alarm.arn
    overall_health = aws_cloudwatch_metric_alarm.overall_health_alarm.arn
  }
}

output "event_rule_arn" {
  description = "EventBridge rule ARN for health check state changes"
  value       = aws_cloudwatch_event_rule.health_check_state_change.arn
}
