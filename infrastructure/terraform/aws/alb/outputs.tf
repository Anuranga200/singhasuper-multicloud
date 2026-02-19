# Outputs for AWS ALB Module

output "alb_id" {
  description = "ID of the Application Load Balancer"
  value       = aws_lb.main.id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_arn_suffix" {
  description = "ARN suffix of the ALB for use with CloudWatch"
  value       = aws_lb.main.arn_suffix
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "backend_target_group_arn" {
  description = "ARN of the backend target group"
  value       = aws_lb_target_group.backend.arn
}

output "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  value       = aws_lb_target_group.frontend.arn
}

output "target_group_arns" {
  description = "List of all target group ARNs"
  value       = [aws_lb_target_group.backend.arn, aws_lb_target_group.frontend.arn]
}

output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = var.certificate_arn != "" ? aws_lb_listener.http.arn : aws_lb_listener.http_dev[0].arn
}

output "https_listener_arn" {
  description = "ARN of the HTTPS listener (if certificate provided)"
  value       = var.certificate_arn != "" ? aws_lb_listener.https[0].arn : null
}
