# Multi-Cloud DR System - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [AWS Deployment](#aws-deployment)
4. [Azure Deployment](#azure-deployment)
5. [GCP Deployment](#gcp-deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

Install the following tools before beginning deployment:

```bash
# Terraform (version 1.5+)
# Download from: https://www.terraform.io/downloads

# AWS CLI (version 2.x)
aws --version

# Azure CLI (version 2.x)
az --version

# Google Cloud SDK
gcloud --version

# Python 3.9+
python --version

# Docker (for local testing)
docker --version
```

### Cloud Provider Accounts

You need active accounts with appropriate permissions on:
- AWS (Administrator or equivalent)
- Microsoft Azure (Contributor or equivalent)
- Google Cloud Platform (Editor or equivalent)

### Required Permissions

#### AWS IAM Permissions
- EC2 full access
- RDS full access
- VPC full access
- Secrets Manager full access
- Route 53 full access
- CloudWatch full access
- IAM role creation

#### Azure RBAC Permissions
- Virtual Machine Contributor
- Network Contributor
- SQL DB Contributor
- Key Vault Administrator

#### GCP IAM Permissions
- Compute Admin
- Cloud SQL Admin
- Secret Manager Admin
- VPC Admin

### Environment Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd infrastructure
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure cloud provider credentials**:

```bash
# AWS
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format

# Azure
az login
az account set --subscription "<subscription-id>"

# GCP
gcloud auth login
gcloud config set project <project-id>
```

## Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] All cloud provider accounts configured
- [ ] Required tools installed and configured
- [ ] Domain name registered (for Route 53)
- [ ] SSL/TLS certificates obtained or ACM configured
- [ ] Budget limits set in each cloud provider
- [ ] Notification email addresses configured
- [ ] Docker image built and pushed to registries
- [ ] Database initialization scripts prepared
- [ ] Backup of any existing data

### Configuration Files

Create configuration files from examples:

```bash
# Terraform variables
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# Backup configuration
cp backup/backup_config.example.json backup/backup_config.json

# Cost monitoring configuration
cp cost/cost_config.example.json cost/cost_config.json

# Monitoring configuration
cp monitoring/monitoring_config.example.json monitoring/monitoring_config.json

# Failover configuration
cp scripts/failover_config.example.json scripts/failover_config.json
```

Edit each configuration file with your specific values.

## AWS Deployment

### Step 1: Configure Terraform Variables

Edit `terraform/terraform.tfvars`:

```hcl
# AWS Configuration
aws_region = "us-east-1"
aws_availability_zones = ["us-east-1a", "us-east-1b"]

# VPC Configuration
aws_vpc_cidr = "10.0.0.0/16"
aws_public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
aws_private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

# EC2 Configuration
aws_instance_type = "t3.micro"
aws_min_instances = 2
aws_max_instances = 10
aws_desired_instances = 2

# RDS Configuration
aws_db_instance_class = "db.t3.micro"
aws_db_name = "appdb"
aws_db_username = "admin"
aws_db_allocated_storage = 20
aws_db_backup_retention_period = 30

# Application Configuration
app_docker_image = "your-registry/your-app:latest"
app_port = 3000

# Domain Configuration
domain_name = "your-domain.com"
```

### Step 2: Initialize Terraform Backend

```bash
cd terraform

# Initialize Terraform
terraform init

# Create S3 bucket for state (if not exists)
aws s3 mb s3://your-terraform-state-bucket --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket your-terraform-state-bucket \
  --versioning-configuration Status=Enabled
```

Update `backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "multi-cloud-dr/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### Step 3: Deploy AWS Infrastructure

```bash
# Navigate to AWS Terraform directory
cd terraform/aws

# Review the plan
terraform plan -out=aws.tfplan

# Apply the configuration
terraform apply aws.tfplan

# Note the outputs
terraform output
```

**Expected outputs**:
- VPC ID
- Subnet IDs
- ALB DNS name
- RDS endpoint
- Secrets Manager ARN

### Step 4: Configure AWS Secrets

```bash
# Store database password
aws secretsmanager create-secret \
  --name /multicloud-dr/db/password \
  --secret-string "your-secure-password" \
  --region us-east-1

# Store JWT secret
aws secretsmanager create-secret \
  --name /multicloud-dr/app/jwt-secret \
  --secret-string "your-jwt-secret" \
  --region us-east-1

# Store API keys
aws secretsmanager create-secret \
  --name /multicloud-dr/app/api-keys \
  --secret-string '{"key1":"value1","key2":"value2"}' \
  --region us-east-1
```

### Step 5: Deploy Application to EC2

The application is automatically deployed via user data script. Verify deployment:

```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test health endpoint
curl https://${ALB_DNS}/health

# Expected response: {"status":"healthy","timestamp":"..."}
```

### Step 6: Initialize Database

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)

# Connect to database
mysql -h ${RDS_ENDPOINT} -u admin -p

# Run initialization script
mysql -h ${RDS_ENDPOINT} -u admin -p appdb < ../scripts/init_database.sql
```

### Step 7: Configure Binary Log Replication

```bash
# Enable binary logging (should already be enabled via Terraform)
# Create replication user
mysql -h ${RDS_ENDPOINT} -u admin -p -e "
CREATE USER 'replication_user'@'%' IDENTIFIED BY 'replication-password';
GRANT REPLICATION SLAVE ON *.* TO 'replication_user'@'%';
FLUSH PRIVILEGES;
"

# Get binary log position
mysql -h ${RDS_ENDPOINT} -u admin -p -e "SHOW MASTER STATUS\G"
```

**Note the output**: File name and Position (needed for Azure and GCP setup)

## Azure Deployment

### Step 1: Configure Azure Variables

Edit `terraform/terraform.tfvars` (Azure section):

```hcl
# Azure Configuration
azure_region = "eastus"
azure_resource_group_name = "multicloud-dr-rg"

# VNet Configuration
azure_vnet_address_space = "10.1.0.0/16"
azure_public_subnet_cidr = "10.1.1.0/24"
azure_private_subnet_cidr = "10.1.11.0/24"

# VM Configuration
azure_vm_size = "Standard_B1s"
azure_vm_count_min = 2
azure_vm_count_max = 10

# MySQL Configuration
azure_mysql_sku = "B_Gen5_1"
azure_mysql_storage_mb = 20480
azure_mysql_backup_retention_days = 30
```

### Step 2: Deploy Azure Infrastructure

```bash
# Navigate to Azure Terraform directory
cd terraform/azure

# Login to Azure (if not already)
az login

# Review the plan
terraform plan -out=azure.tfplan

# Apply the configuration
terraform apply azure.tfplan

# Note the outputs
terraform output
```

**Expected outputs**:
- Resource Group name
- VNet ID
- Load Balancer public IP
- MySQL server name
- Key Vault name

### Step 3: Configure Azure Key Vault

```bash
# Get Key Vault name
KEYVAULT_NAME=$(terraform output -raw keyvault_name)

# Store database password
az keyvault secret set \
  --vault-name ${KEYVAULT_NAME} \
  --name db-password \
  --value "your-secure-password"

# Store JWT secret
az keyvault secret set \
  --vault-name ${KEYVAULT_NAME} \
  --name jwt-secret \
  --value "your-jwt-secret"

# Store API keys
az keyvault secret set \
  --vault-name ${KEYVAULT_NAME} \
  --name api-keys \
  --value '{"key1":"value1","key2":"value2"}'
```

### Step 4: Configure Database Replication

```bash
# Get Azure MySQL server name
AZURE_MYSQL_SERVER=$(terraform output -raw mysql_server_name)

# Get AWS RDS endpoint and binary log position from Step 7 of AWS deployment
AWS_RDS_ENDPOINT="<from-aws-output>"
BINLOG_FILE="<from-aws-output>"
BINLOG_POSITION="<from-aws-output>"

# Connect to Azure MySQL
mysql -h ${AZURE_MYSQL_SERVER}.mysql.database.azure.com -u admin@${AZURE_MYSQL_SERVER} -p

# Configure replication
CHANGE MASTER TO
  MASTER_HOST='${AWS_RDS_ENDPOINT}',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='replication-password',
  MASTER_LOG_FILE='${BINLOG_FILE}',
  MASTER_LOG_POS=${BINLOG_POSITION};

# Start replication
START SLAVE;

# Verify replication status
SHOW SLAVE STATUS\G
```

**Verify**: `Slave_IO_Running: Yes` and `Slave_SQL_Running: Yes`

### Step 5: Deploy Application to VMs

The application is automatically deployed via custom script extension. Verify:

```bash
# Get Load Balancer public IP
LB_IP=$(terraform output -raw lb_public_ip)

# Test health endpoint
curl https://${LB_IP}/health
```

## GCP Deployment

### Step 1: Configure GCP Variables

Edit `terraform/terraform.tfvars` (GCP section):

```hcl
# GCP Configuration
gcp_project_id = "your-project-id"
gcp_region = "us-central1"
gcp_zones = ["us-central1-a", "us-central1-b"]

# VPC Configuration
gcp_vpc_subnet_cidr = "10.2.0.0/16"
gcp_public_subnet_cidr = "10.2.1.0/24"
gcp_private_subnet_cidr = "10.2.11.0/24"

# Compute Configuration
gcp_machine_type = "e2-micro"
gcp_min_instances = 2
gcp_max_instances = 10

# Cloud SQL Configuration
gcp_db_tier = "db-f1-micro"
gcp_db_disk_size = 20
gcp_db_backup_enabled = true
```

### Step 2: Enable Required APIs

```bash
# Enable required GCP APIs
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### Step 3: Deploy GCP Infrastructure

```bash
# Navigate to GCP Terraform directory
cd terraform/gcp

# Review the plan
terraform plan -out=gcp.tfplan

# Apply the configuration
terraform apply gcp.tfplan

# Note the outputs
terraform output
```

**Expected outputs**:
- VPC network name
- Load Balancer IP
- Cloud SQL instance name
- Secret Manager project

### Step 4: Configure GCP Secret Manager

```bash
# Store database password
echo -n "your-secure-password" | gcloud secrets create db-password \
  --data-file=- \
  --replication-policy="automatic"

# Store JWT secret
echo -n "your-jwt-secret" | gcloud secrets create jwt-secret \
  --data-file=- \
  --replication-policy="automatic"

# Store API keys
echo -n '{"key1":"value1","key2":"value2"}' | gcloud secrets create api-keys \
  --data-file=- \
  --replication-policy="automatic"
```

### Step 5: Configure Database Replication

```bash
# Get Cloud SQL instance name
GCP_SQL_INSTANCE=$(terraform output -raw cloudsql_instance_name)

# Get AWS RDS endpoint and binary log position
AWS_RDS_ENDPOINT="<from-aws-output>"
BINLOG_FILE="<from-aws-output>"
BINLOG_POSITION="<from-aws-output>"

# Connect to Cloud SQL
gcloud sql connect ${GCP_SQL_INSTANCE} --user=root

# Configure replication
CHANGE MASTER TO
  MASTER_HOST='${AWS_RDS_ENDPOINT}',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='replication-password',
  MASTER_LOG_FILE='${BINLOG_FILE}',
  MASTER_LOG_POS=${BINLOG_POSITION};

# Start replication
START SLAVE;

# Verify replication status
SHOW SLAVE STATUS\G
```

**Verify**: `Slave_IO_Running: Yes` and `Slave_SQL_Running: Yes`

### Step 6: Deploy Application to Compute Instances

The application is automatically deployed via startup script. Verify:

```bash
# Get Load Balancer IP
LB_IP=$(terraform output -raw lb_ip_address)

# Test health endpoint
curl https://${LB_IP}/health
```

## Post-Deployment Configuration

### Step 1: Configure Route 53 DNS

```bash
cd terraform/route53

# Update variables with endpoints from all clouds
terraform plan -out=route53.tfplan
terraform apply route53.tfplan

# Get hosted zone ID
HOSTED_ZONE_ID=$(terraform output -raw hosted_zone_id)

# Verify health checks
aws route53 get-health-check-status --health-check-id <health-check-id>
```

### Step 2: Set Up Monitoring Dashboards

```bash
cd ../monitoring

# Configure monitoring
cp monitoring_config.example.json monitoring_config.json
# Edit with your endpoints and credentials

# Create AWS CloudWatch dashboard
python aws_cloudwatch_dashboard.py

# Create Azure Monitor dashboard
python azure_monitor_dashboard.py

# Create GCP Cloud Monitoring dashboard
python gcp_monitoring_dashboard.py

# Create unified dashboard
python unified_dashboard.py
```

### Step 3: Configure Health Monitoring

```bash
cd ../scripts

# Configure health monitor
cp failover_config.example.json failover_config.json
# Edit with your endpoints

# Start health monitor (run as service)
python health_monitor.py &

# Verify health monitor is running
ps aux | grep health_monitor
```

### Step 4: Set Up Backup Automation

```bash
cd ../backup

# Configure backup manager
cp backup_config.example.json backup_config.json
# Edit with your database endpoints

# Test backup creation
python backup_manager.py --test

# Schedule daily backups (add to crontab)
crontab -e
# Add: 0 2 * * * /usr/bin/python3 /path/to/backup_manager.py
```

### Step 5: Configure Cost Monitoring

```bash
cd ../cost

# Configure cost monitor
cp cost_config.example.json cost_config.json
# Edit with your cloud credentials

# Test cost retrieval
python cost_monitor.py --test

# Schedule daily cost collection (add to crontab)
crontab -e
# Add: 0 8 * * * /usr/bin/python3 /path/to/cost_monitor.py
```

### Step 6: Set Up Alerting

```bash
# Configure SNS topic for alerts (AWS)
aws sns create-topic --name multicloud-dr-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:multicloud-dr-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Confirm subscription via email

# Configure SMS alerts (optional)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:multicloud-dr-alerts \
  --protocol sms \
  --notification-endpoint +1234567890
```

## Verification

### Step 1: Run Deployment Verification Script

```bash
cd ../tests

# Run comprehensive verification
python verify_deployment.py

# Expected output: All checks should pass
```

### Step 2: Test Application Functionality

```bash
# Get application URL
APP_URL="https://your-domain.com"

# Test health endpoint
curl ${APP_URL}/health

# Test application endpoints
curl -X POST ${APP_URL}/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User"}'

# Verify data in database
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p -e "SELECT * FROM appdb.users;"
```

### Step 3: Verify Database Replication

```bash
# Run consistency verification
cd ../scripts
python verify_consistency.py

# Check replication lag
python setup_replication.py --check-lag
```

### Step 4: Test Failover Mechanism

```bash
# Simulate AWS failure (manual test)
# Stop AWS EC2 instances via console

# Monitor DNS failover
watch -n 5 'dig your-domain.com +short'

# Verify traffic routes to Azure
curl https://your-domain.com/health

# Restore AWS and verify failback
```

### Step 5: Run Property-Based Tests

```bash
cd ../tests/property

# Run all property tests
pytest test_*.py -v

# Run specific test suites
pytest test_aws_deployment.py -v
pytest test_dns_routing.py -v
pytest test_failover_orchestration.py -v
```

## Troubleshooting

### Common Issues

#### Issue 1: Terraform Apply Fails

**Symptoms**: Terraform errors during apply

**Solutions**:
```bash
# Check credentials
aws sts get-caller-identity
az account show
gcloud auth list

# Verify permissions
# Ensure IAM roles have required permissions

# Check resource limits
# Verify you haven't hit service quotas

# Clean up and retry
terraform destroy
terraform apply
```

#### Issue 2: Database Replication Not Working

**Symptoms**: `Slave_IO_Running: No` or `Slave_SQL_Running: No`

**Solutions**:
```bash
# Check network connectivity
telnet ${AWS_RDS_ENDPOINT} 3306

# Verify replication user
mysql -h ${AWS_RDS_ENDPOINT} -u replication_user -p

# Check binary log position
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p -e "SHOW MASTER STATUS\G"

# Reset replication
STOP SLAVE;
RESET SLAVE;
# Reconfigure with correct position
CHANGE MASTER TO ...
START SLAVE;
```

#### Issue 3: Health Checks Failing

**Symptoms**: Route 53 health checks show unhealthy

**Solutions**:
```bash
# Test endpoint directly
curl -v https://${ALB_DNS}/health

# Check security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Verify application is running
aws ec2 describe-instances --filters "Name=tag:Name,Values=multicloud-dr-*"

# Check application logs
aws logs tail /aws/ec2/multicloud-dr --follow
```

#### Issue 4: Application Can't Connect to Database

**Symptoms**: Application errors, database connection failures

**Solutions**:
```bash
# Verify security group rules
# Ensure application security group can access database security group

# Check database endpoint
aws rds describe-db-instances --db-instance-identifier <instance-id>

# Test connection from EC2
mysql -h ${RDS_ENDPOINT} -u admin -p

# Verify secrets are accessible
aws secretsmanager get-secret-value --secret-id /multicloud-dr/db/password
```

#### Issue 5: High Costs

**Symptoms**: Cloud bills higher than expected

**Solutions**:
```bash
# Check running resources
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
az vm list --query "[].{Name:name, State:powerState}"
gcloud compute instances list

# Review cost reports
python ../cost/cost_reporter.py --detailed

# Identify unused resources
# Stop non-production environments
# Resize over-provisioned instances
```

### Getting Help

If you encounter issues not covered here:

1. Check the logs:
   - AWS CloudWatch Logs
   - Azure Monitor Logs
   - GCP Cloud Logging

2. Review the architecture documentation: `docs/ARCHITECTURE.md`

3. Consult the troubleshooting guide: `docs/runbooks/TROUBLESHOOTING.md`

4. Contact the operations team with:
   - Error messages
   - Relevant logs
   - Steps to reproduce

## Next Steps

After successful deployment:

1. Review operational runbooks in `docs/runbooks/`
2. Schedule regular DR drills
3. Set up monitoring alerts
4. Document any customizations
5. Train operations team on failover procedures

## Deployment Checklist

Use this checklist to track deployment progress:

- [ ] Prerequisites installed and configured
- [ ] AWS infrastructure deployed
- [ ] AWS secrets configured
- [ ] AWS application deployed and verified
- [ ] Azure infrastructure deployed
- [ ] Azure secrets configured
- [ ] Azure replication configured
- [ ] Azure application deployed and verified
- [ ] GCP infrastructure deployed
- [ ] GCP secrets configured
- [ ] GCP replication configured
- [ ] GCP application deployed and verified
- [ ] Route 53 DNS configured
- [ ] Health monitoring configured
- [ ] Backup automation configured
- [ ] Cost monitoring configured
- [ ] Alerting configured
- [ ] Monitoring dashboards created
- [ ] Verification tests passed
- [ ] Failover test completed
- [ ] Documentation reviewed
- [ ] Team trained

## Conclusion

You now have a fully deployed multi-cloud disaster recovery system. Regular testing and monitoring are essential to ensure the system functions correctly during an actual disaster scenario.
