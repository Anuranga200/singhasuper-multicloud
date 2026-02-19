# Outputs for AWS Main Deployment

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the ALB for Route 53"
  value       = module.alb.alb_zone_id
}

output "db_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "db_secret_arn" {
  description = "ARN of database credentials secret"
  value       = module.rds.secret_arn
}

output "app_secret_arn" {
  description = "ARN of application secrets"
  value       = module.secrets.app_secrets_arn
}

output "health_check_id" {
  description = "ID of Route 53 health check"
  value       = aws_route53_health_check.primary.id
}

output "sns_topic_arn" {
  description = "ARN of SNS topic for alerts"
  value       = module.sns.topic_arn
}

output "autoscaling_group_name" {
  description = "Name of the Auto Scaling Group"
  value       = module.ec2.autoscaling_group_name
}

output "dashboard_name" {
  description = "Name of CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}
