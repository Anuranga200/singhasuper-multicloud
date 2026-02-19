# AWS Secrets Manager Module for Multi-Cloud DR System
# Stores application secrets with automatic rotation

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Secret for Application Secrets (JWT, API keys)
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}-${var.environment}-app-secrets"
  description = "Application secrets including JWT keys and API tokens"

  recovery_window_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-app-secrets"
    }
  )
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    jwt_secret         = var.jwt_secret
    jwt_refresh_secret = var.jwt_refresh_secret
    api_key            = var.api_key
    cors_origin        = var.cors_origin
  })
}

# Lambda function for database credential rotation
resource "aws_lambda_function" "rotate_db_credentials" {
  filename      = "${path.module}/lambda/rotate_credentials.zip"
  function_name = "${var.project_name}-${var.environment}-rotate-db-creds"
  role          = aws_iam_role.lambda_rotation.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 30

  environment {
    variables = {
      DB_SECRET_ARN = var.db_secret_arn
    }
  }

  tags = var.tags
}

# IAM Role for Lambda rotation function
resource "aws_iam_role" "lambda_rotation" {
  name = "${var.project_name}-${var.environment}-lambda-rotation-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Policy for Lambda to rotate secrets
resource "aws_iam_role_policy" "lambda_rotation" {
  name = "${var.project_name}-${var.environment}-lambda-rotation-policy"
  role = aws_iam_role.lambda_rotation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = [
          aws_secretsmanager_secret.app_secrets.arn,
          var.db_secret_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetRandomPassword"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:ModifyDBInstance"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda permission for Secrets Manager to invoke
resource "aws_lambda_permission" "allow_secrets_manager" {
  statement_id  = "AllowExecutionFromSecretsManager"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rotate_db_credentials.function_name
  principal     = "secretsmanager.amazonaws.com"
}

# EventBridge rule for scheduled rotation (every 90 days)
resource "aws_cloudwatch_event_rule" "rotate_secrets" {
  name                = "${var.project_name}-${var.environment}-rotate-secrets"
  description         = "Trigger secret rotation every 90 days"
  schedule_expression = "rate(90 days)"

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "rotate_secrets" {
  rule      = aws_cloudwatch_event_rule.rotate_secrets.name
  target_id = "RotateSecretsLambda"
  arn       = aws_lambda_function.rotate_db_credentials.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rotate_db_credentials.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rotate_secrets.arn
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_rotation" {
  name              = "/aws/lambda/${aws_lambda_function.rotate_db_credentials.function_name}"
  retention_in_days = 90

  tags = var.tags
}

# SNS Topic for secret rotation notifications
resource "aws_sns_topic" "secret_rotation" {
  name = "${var.project_name}-${var.environment}-secret-rotation"

  tags = var.tags
}

resource "aws_sns_topic_subscription" "secret_rotation_email" {
  count = var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.secret_rotation.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarm for failed rotations
resource "aws_cloudwatch_metric_alarm" "rotation_failures" {
  alarm_name          = "${var.project_name}-${var.environment}-secret-rotation-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors secret rotation failures"
  alarm_actions       = [aws_sns_topic.secret_rotation.arn]

  dimensions = {
    FunctionName = aws_lambda_function.rotate_db_credentials.function_name
  }

  tags = var.tags
}
