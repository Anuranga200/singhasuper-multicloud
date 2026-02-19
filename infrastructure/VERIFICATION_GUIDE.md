# Deployment Verification Guide

This guide walks you through verifying that your multi-cloud DR system is properly deployed and operational.

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to infrastructure directory
cd infrastructure

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Cloud Credentials

#### AWS
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Azure
```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"

# Or set environment variable
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
```

#### GCP
```bash
# Login to GCP
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project your-project-id

# Or set environment variable
export GCP_PROJECT_ID="your-project-id"
```

### 3. Run Automated Verification

```bash
# Run the verification script
python tests/verify_deployment.py
```

This script will:
- ✓ Check AWS infrastructure components
- ✓ Check Azure infrastructure components
- ✓ Check GCP infrastructure components
- ✓ Run property-based tests
- ✓ Generate a summary report

### 4. Review Results

The script will output:
- **Green ✓**: Component exists and is properly configured
- **Red ✗**: Component missing or misconfigured
- **Yellow ⚠**: Warning or optional component

## Manual Verification Steps

If you prefer to verify manually or need to troubleshoot specific components:

### AWS Verification

```bash
# Check VPC
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=singha-loyalty-prod-vpc"

# Check RDS
aws rds describe-db-instances --db-instance-identifier singha-loyalty-prod-mysql

# Check Auto Scaling Group
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names singha-loyalty-prod-asg

# Check Load Balancer
aws elbv2 describe-load-balancers --names singha-loyalty-prod-alb

# Check Secrets
aws secretsmanager list-secrets --filters Key=name,Values=singha-loyalty-prod
```

### Azure Verification

```bash
# Check Resource Group
az group show --name singha-loyalty-prod-rg

# Check VNet
az network vnet show --resource-group singha-loyalty-prod-rg --name singha-loyalty-prod-vnet

# Check MySQL
az mysql flexible-server show --resource-group singha-loyalty-prod-rg --name singha-loyalty-prod-mysql

# Check VMSS
az vmss show --resource-group singha-loyalty-prod-rg --name singha-loyalty-prod-vmss

# Check Load Balancer
az network lb show --resource-group singha-loyalty-prod-rg --name singha-loyalty-prod-lb

# Check Key Vault
az keyvault show --name singha-loyalty-prod-kv
```

### GCP Verification

```bash
# Check VPC
gcloud compute networks describe singha-loyalty-prod-vpc

# Check Cloud SQL
gcloud sql instances describe singha-loyalty-prod-mysql

# Check Instance Group
gcloud compute instance-groups managed describe singha-loyalty-prod-igm --region us-central1

# Check Load Balancer
gcloud compute forwarding-rules list --filter="name:singha-loyalty-prod"

# Check Secrets
gcloud secrets list --filter="name:singha-loyalty-prod"
```

## Running Property-Based Tests

### Run All Tests

```bash
# Run all property tests
pytest tests/property/ -v

# Run with coverage
pytest tests/property/ --cov=infrastructure --cov-report=html

# Run specific cloud tests
pytest tests/property/test_aws_deployment.py -v
pytest tests/property/test_azure_deployment.py -v
pytest tests/property/test_gcp_deployment.py -v
```

### Run Individual Test Functions

```bash
# Run specific test
pytest tests/property/test_aws_deployment.py::test_property_1_example_production -v

# Run with detailed output
pytest tests/property/test_aws_deployment.py -v -s
```

## Troubleshooting

### AWS Issues

**Issue**: "AWS credentials not configured"
```bash
# Solution: Configure AWS CLI
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

**Issue**: "VPC not found"
```bash
# Check if VPC exists
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=singha-loyalty"

# Check Terraform state
cd terraform/aws
terraform state list
terraform state show module.vpc.aws_vpc.main
```

**Issue**: "RDS instance not found"
```bash
# List all RDS instances
aws rds describe-db-instances

# Check specific instance
aws rds describe-db-instances --db-instance-identifier singha-loyalty-prod-mysql
```

### Azure Issues

**Issue**: "Azure credentials not configured"
```bash
# Solution: Login to Azure
az login
az account set --subscription "your-subscription-id"
```

**Issue**: "Resource group not found"
```bash
# List all resource groups
az group list --output table

# Check if resource group exists
az group exists --name singha-loyalty-prod-rg
```

**Issue**: "MySQL server not found"
```bash
# List all MySQL servers
az mysql flexible-server list --output table

# Check specific server
az mysql flexible-server show --resource-group singha-loyalty-prod-rg --name singha-loyalty-prod-mysql
```

### GCP Issues

**Issue**: "GCP credentials not configured"
```bash
# Solution: Login to GCP
gcloud auth login
gcloud auth application-default login
gcloud config set project your-project-id
```

**Issue**: "VPC not found"
```bash
# List all VPCs
gcloud compute networks list

# Check specific VPC
gcloud compute networks describe singha-loyalty-prod-vpc
```

**Issue**: "Cloud SQL instance not found"
```bash
# List all Cloud SQL instances
gcloud sql instances list

# Check specific instance
gcloud sql instances describe singha-loyalty-prod-mysql
```

### Python Dependency Issues

**Issue**: "ModuleNotFoundError: No module named 'boto3'"
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Or install specific package
pip install boto3
```

**Issue**: "ImportError: cannot import name 'DefaultAzureCredential'"
```bash
# Solution: Install Azure SDK
pip install azure-identity azure-mgmt-resource azure-mgmt-network
```

## Verification Checklist

Use the comprehensive checklist to track your verification progress:

```bash
# Open the checklist
cat DEPLOYMENT_CHECKLIST.md
```

The checklist covers:
- ✓ Prerequisites (CLI tools, credentials)
- ✓ AWS infrastructure components
- ✓ Azure infrastructure components
- ✓ GCP infrastructure components
- ✓ Cross-cloud connectivity
- ✓ Database replication
- ✓ DNS and routing
- ✓ Security controls
- ✓ Monitoring and alerts
- ✓ Testing
- ✓ Cost verification
- ✓ Documentation

## Next Steps

After verification passes:

1. **Test Application Access**
   ```bash
   # Get AWS ALB DNS name
   aws elbv2 describe-load-balancers --names singha-loyalty-prod-alb --query 'LoadBalancers[0].DNSName'
   
   # Test application
   curl https://your-alb-dns-name/health
   ```

2. **Verify Database Replication**
   - Write data to AWS primary
   - Check data appears in Azure replica
   - Check data appears in GCP replica
   - Measure replication lag

3. **Test Failover**
   - Simulate AWS failure
   - Verify automatic failover to Azure
   - Measure RTO (should be < 5 minutes)

4. **Review Monitoring**
   - Check CloudWatch dashboards
   - Verify alerts are configured
   - Test alert notifications

5. **Proceed to Task 6**
   - Database replication setup
   - Cross-cloud replication configuration
   - Replication monitoring

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review Terraform logs: `terraform show`
3. Check cloud provider console for resource status
4. Review property test output for specific failures
5. Consult the deployment checklist for missing steps

## Summary

This verification ensures:
- ✓ All infrastructure is deployed correctly
- ✓ Components are properly configured
- ✓ Security controls are in place
- ✓ Monitoring is operational
- ✓ System is ready for the next phase

Once verification passes, you're ready to proceed with database replication setup (Task 6).
