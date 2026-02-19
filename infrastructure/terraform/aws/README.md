# AWS Primary Cloud Infrastructure

This directory contains Terraform modules for deploying the Singha Loyalty System on AWS as the primary active cloud.

## Architecture Overview

The AWS deployment includes:
- **VPC**: Multi-AZ VPC with public and private subnets
- **RDS MySQL**: Multi-AZ MySQL 8.0 database with automated backups
- **EC2 Auto Scaling**: Docker-enabled instances with auto-scaling
- **Application Load Balancer**: HTTPS-enabled ALB with health checks
- **Secrets Manager**: Secure storage for credentials with rotation
- **CloudWatch**: Monitoring, logging, and alerting
- **SNS**: Email and SMS notifications

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0
3. **Docker image** pushed to a container registry
4. **ACM Certificate** (optional, for HTTPS)

## Quick Start

### 1. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Plan Deployment

```bash
terraform plan -out=tfplan
```

### 4. Apply Configuration

```bash
terraform apply tfplan
```

## Module Structure

```
aws/
├── main.tf              # Main orchestration file
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── vpc/                 # VPC and networking module
├── rds/                 # RDS MySQL module
├── ec2/                 # EC2 Auto Scaling module
├── alb/                 # Application Load Balancer module
├── secrets/             # Secrets Manager module
└── sns/                 # SNS notifications module
```

## Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `docker_image` | Docker image URL | `123456789.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest` |
| `db_username` | Database master username | `admin` |
| `db_password` | Database master password | `SecurePassword123!` |
| `jwt_secret` | JWT secret key | `random-secret-key-here` |
| `jwt_refresh_secret` | JWT refresh secret | `random-refresh-secret-here` |
| `alert_email` | Email for alerts | `devops@example.com` |

## Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region | `us-east-1` |
| `aws_instance_type` | EC2 instance type | `t3.micro` |
| `aws_db_instance_class` | RDS instance class | `db.t3.micro` |
| `certificate_arn` | ACM certificate ARN | `""` (HTTP only) |
| `min_instances` | Min ASG instances | `2` |
| `max_instances` | Max ASG instances | `4` |

## Post-Deployment Steps

### 1. Verify Deployment

```bash
# Get ALB DNS name
terraform output alb_dns_name

# Test health endpoint
curl http://$(terraform output -raw alb_dns_name)/health
```

### 2. Configure DNS

Point your domain to the ALB DNS name using a CNAME record:

```
app.example.com CNAME <alb-dns-name>
```

### 3. Run Database Migrations

```bash
# SSH into an EC2 instance (via Systems Manager)
aws ssm start-session --target <instance-id>

# Run migrations
cd /opt/singha-loyalty
docker-compose exec backend npm run migrate
```

### 4. Verify Monitoring

```bash
# Open CloudWatch dashboard
aws cloudwatch get-dashboard \
  --dashboard-name $(terraform output -raw dashboard_name)
```

## Cost Estimation

Monthly costs for AWS primary deployment:

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| EC2 (t3.micro x2) | 2 instances, 24/7 | $15/month |
| RDS (db.t3.micro) | Multi-AZ, 20GB | $25/month |
| ALB | Standard ALB | $20/month |
| Data Transfer | ~100GB/month | $10/month |
| CloudWatch | Logs + metrics | $5/month |
| Secrets Manager | 2 secrets | $1/month |
| **Total** | | **~$76/month** |

## Security Features

- ✅ VPC with private subnets for app and database
- ✅ Security groups with least privilege rules
- ✅ Secrets Manager for credential storage
- ✅ Encrypted RDS storage
- ✅ TLS 1.2+ enforcement on ALB
- ✅ IAM roles with minimal permissions
- ✅ Automated credential rotation (90 days)
- ✅ CloudWatch logging enabled

## Monitoring and Alerts

### CloudWatch Alarms

The deployment creates alarms for:
- RDS CPU utilization > 80%
- RDS free memory < 256MB
- RDS free storage < 2GB
- EC2 CPU utilization > 80%
- ALB target response time > 1s
- ALB unhealthy hosts > 0
- ALB 5XX errors > 10

### SNS Notifications

Alerts are sent to:
- Email (configured via `alert_email`)
- SMS (optional, via `alert_phone`)

## Backup and Recovery

### Automated Backups

- **RDS**: Daily automated backups, 30-day retention
- **Point-in-time recovery**: 7 days
- **Backup window**: 03:00-04:00 UTC
- **Maintenance window**: Monday 04:00-05:00 UTC

### Manual Backup

```bash
# Create manual RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier singha-loyalty-prod-mysql \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d)
```

### Restore from Backup

```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier singha-loyalty-restored \
  --db-snapshot-identifier <snapshot-id>
```

## Scaling

### Manual Scaling

```bash
# Scale up ASG
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name $(terraform output -raw autoscaling_group_name) \
  --desired-capacity 4
```

### Auto Scaling

Auto Scaling is configured to:
- Target 70% CPU utilization
- Scale between 2-4 instances
- Cooldown period: 300 seconds

## Troubleshooting

### Application Not Accessible

1. Check ALB health checks:
```bash
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>
```

2. Check EC2 instance logs:
```bash
aws ssm start-session --target <instance-id>
docker-compose logs
```

### Database Connection Issues

1. Verify security group rules
2. Check RDS endpoint:
```bash
terraform output db_endpoint
```

3. Test connection from EC2:
```bash
mysql -h <db-endpoint> -u admin -p
```

### High Costs

1. Review CloudWatch dashboard
2. Check for unused resources:
```bash
# List stopped instances
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=stopped"
```

3. Review RDS storage auto-scaling

## Cleanup

To destroy all resources:

```bash
# Disable deletion protection first
terraform apply -var="enable_deletion_protection=false"

# Destroy all resources
terraform destroy
```

**Warning**: This will delete all data. Ensure backups are taken before destroying.

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review CloudWatch Alarms
3. Check SNS notifications
4. Refer to troubleshooting guides in `docs/troubleshooting/`
