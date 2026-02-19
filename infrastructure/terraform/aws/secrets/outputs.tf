# Outputs for AWS Secrets Manager Module

output "app_secrets_arn" {
  description = "ARN of the application secrets"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "app_secrets_name" {
  description = "Name of the application secrets"
  value       = aws_secretsmanager_secret.app_secrets.name
}

output "rotation_lambda_arn" {
  description = "ARN of the rotation Lambda function"
  value       = aws_lambda_function.rotate_db_credentials.arn
}

output "rotation_lambda_name" {
  description = "Name of the rotation Lambda function"
  value       = aws_lambda_function.rotate_db_credentials.function_name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for rotation notifications"
  value       = aws_sns_topic.secret_rotation.arn
}
