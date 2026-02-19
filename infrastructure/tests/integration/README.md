# Integration Tests

## Overview

This directory contains end-to-end integration tests for the Multi-Cloud Disaster Recovery System. These tests verify that all components work together correctly across AWS, Azure, and GCP.

## Test Suites

### 1. test_failover_aws_to_azure.py
**Purpose**: Test complete failover from AWS to Azure

**What it tests**:
- AWS health verification
- Test data write to primary
- AWS failure simulation
- Automated failover to Azure
- Azure serving traffic
- Application functionality on Azure
- RTO and RPO measurement

**Duration**: ~10-15 minutes

**Requirements tested**:
- 2.2: Automated failover to Azure
- 2.7: RTO < 5 minutes
- 3.5: RPO < 1 minute

**Usage**:
```bash
python test_failover_aws_to_azure.py
```

### 2. test_failover_aws_to_gcp.py
**Purpose**: Test cascade failover from AWS to GCP

**What it tests**:
- AWS and Azure failure simulation
- Cascade failover to GCP
- GCP serving traffic
- Application functionality on GCP
- RTO and RPO measurement

**Duration**: ~10-15 minutes

**Requirements tested**:
- 2.3: Cascade failover to GCP
- 2.7: RTO < 5 minutes
- 3.5: RPO < 1 minute

**Usage**:
```bash
python test_failover_aws_to_gcp.py
```

### 3. test_database_replication.py
**Purpose**: Test database replication across all clouds

**What it tests**:
- Data write to AWS primary
- Replication to Azure replica
- Replication to GCP replica
- Replication lag measurement
- Data consistency verification
- Replication under load

**Duration**: ~5-10 minutes

**Requirements tested**:
- 3.1: Replication lag < 30 seconds (Azure)
- 3.2: Replication lag < 30 seconds (GCP)
- 3.6: Data consistency verification

**Usage**:
```bash
python test_database_replication.py
```

### 4. test_security_controls.py
**Purpose**: Test security controls across all clouds

**What it tests**:
- No secrets in logs
- Network isolation
- TLS enforcement
- IAM least privilege
- Secrets in secret managers
- Encryption at rest
- Minimal firewall rules

**Duration**: ~5-10 minutes

**Requirements tested**:
- 4.1: Least privilege IAM
- 4.2: Secrets in secret managers
- 4.4: TLS 1.2+ enforcement
- 4.6: Minimal firewall rules
- 4.7: Encryption at rest

**Usage**:
```bash
python test_security_controls.py
```

## Prerequisites

### Required Tools
- Python 3.9+
- AWS CLI configured
- Azure CLI configured
- Google Cloud SDK configured
- MySQL client

### Required Python Packages
```bash
pip install boto3 azure-identity azure-mgmt-compute azure-mgmt-network google-cloud-compute google-cloud-sql mysql-connector-python requests
```

### Required Permissions

**AWS**:
- EC2: DescribeInstances, StopInstances, StartInstances
- RDS: DescribeDBInstances
- Auto Scaling: DescribeAutoScalingGroups, SuspendProcesses, ResumeProcesses
- Route 53: GetHealthCheckStatus, ChangeResourceRecordSets
- Secrets Manager: DescribeSecret, GetSecretValue
- IAM: ListRoles, ListAttachedRolePolicies
- CloudWatch Logs: FilterLogEvents

**Azure**:
- Virtual Machine Contributor
- Network Contributor
- Key Vault Reader
- MySQL Server Contributor

**GCP**:
- Compute Admin
- Cloud SQL Admin
- Secret Manager Secret Accessor

### Environment Variables

Set these environment variables before running tests:

```bash
# Database passwords
export AWS_DB_PASSWORD="your-aws-db-password"
export AZURE_DB_PASSWORD="your-azure-db-password"
export GCP_DB_PASSWORD="your-gcp-db-password"

# Cloud credentials (if not using CLI profiles)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export GCP_PROJECT_ID="your-project-id"
```

## Configuration

Each test file has a `TEST_CONFIG` dictionary at the top. Update these values to match your deployment:

```python
TEST_CONFIG = {
    'aws': {
        'region': 'us-east-1',
        'alb_dns': 'your-alb-dns',
        'rds_endpoint': 'your-rds-endpoint',
        'asg_name': 'your-asg-name'
    },
    'azure': {
        'subscription_id': 'your-subscription-id',
        'resource_group': 'your-resource-group',
        'lb_ip': 'your-lb-ip',
        'mysql_server': 'your-mysql-server'
    },
    'gcp': {
        'project_id': 'your-project-id',
        'region': 'us-central1',
        'lb_ip': 'your-lb-ip',
        'cloudsql_instance': 'your-cloudsql-instance'
    }
}
```

## Running Tests

### Run Individual Test
```bash
cd infrastructure/tests/integration
python test_failover_aws_to_azure.py
```

### Run All Tests
```bash
cd infrastructure/tests/integration
for test in test_*.py; do
    echo "Running $test..."
    python "$test"
    if [ $? -ne 0 ]; then
        echo "Test $test failed!"
        exit 1
    fi
done
echo "All tests passed!"
```

### Run with Pytest
```bash
pytest test_*.py -v
```

## Test Output

Each test generates detailed output including:
- Test progress logs with timestamps
- Pass/fail status for each test step
- Warnings for non-critical issues
- Metrics (RTO, RPO, replication lag, etc.)
- Final test report

Example output:
```
[2024-01-15 10:30:00] [INFO] ================================================================================
[2024-01-15 10:30:00] [INFO] INTEGRATION TEST: AWS to Azure Failover
[2024-01-15 10:30:00] [INFO] ================================================================================
[2024-01-15 10:30:01] [INFO] ================================================================================
[2024-01-15 10:30:01] [INFO] TEST 1: Verify AWS is Healthy
[2024-01-15 10:30:01] [INFO] ================================================================================
[2024-01-15 10:30:02] [PASSED] AWS ALB health check passed
[2024-01-15 10:30:03] [PASSED] AWS RDS status: available
[2024-01-15 10:30:04] [PASSED] AWS has 2 healthy instances
...
[2024-01-15 10:45:00] [INFO] ================================================================================
[2024-01-15 10:45:00] [INFO] TEST REPORT
[2024-01-15 10:45:00] [INFO] ================================================================================
[2024-01-15 10:45:00] [INFO] Test Duration: 900.00 seconds
[2024-01-15 10:45:00] [INFO] Passed: 25
[2024-01-15 10:45:00] [INFO] Failed: 0
[2024-01-15 10:45:00] [INFO] Warnings: 2
[2024-01-15 10:45:00] [INFO] 
[2024-01-15 10:45:00] [INFO] Metrics:
[2024-01-15 10:45:00] [INFO]   rto_seconds: 285.5
[2024-01-15 10:45:00] [INFO]   rto_minutes: 4.76
[2024-01-15 10:45:00] [INFO]   rpo_seconds: 25.3
[2024-01-15 10:45:00] [INFO] 
[2024-01-15 10:45:00] [INFO] ✓ INTEGRATION TEST PASSED
```

## Troubleshooting

### Test Fails to Connect to Database
**Problem**: `Database connection error: Can't connect to MySQL server`

**Solutions**:
1. Verify database endpoints in TEST_CONFIG
2. Check security groups allow your IP
3. Verify database passwords in environment variables
4. Test connection manually: `mysql -h <endpoint> -u <user> -p`

### Test Times Out
**Problem**: Test exceeds timeout and fails

**Solutions**:
1. Increase timeout values in test configuration
2. Check cloud resources are running
3. Verify network connectivity
4. Check for rate limiting

### AWS Credentials Error
**Problem**: `Unable to locate credentials`

**Solutions**:
1. Run `aws configure` to set up credentials
2. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
3. Verify IAM permissions

### Azure Authentication Error
**Problem**: `DefaultAzureCredential failed to retrieve a token`

**Solutions**:
1. Run `az login` to authenticate
2. Set AZURE_SUBSCRIPTION_ID environment variable
3. Verify Azure CLI is installed

### GCP Authentication Error
**Problem**: `Application Default Credentials are not available`

**Solutions**:
1. Run `gcloud auth application-default login`
2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable
3. Verify gcloud SDK is installed

## Best Practices

### Before Running Tests
1. Verify all cloud resources are deployed and healthy
2. Ensure you have necessary permissions
3. Set all required environment variables
4. Review and update TEST_CONFIG values
5. Run tests in a non-production environment first

### During Tests
1. Monitor cloud consoles for resource status
2. Watch for cost implications (tests create/modify resources)
3. Don't interrupt tests mid-execution (can leave resources in bad state)
4. Save test output for analysis

### After Tests
1. Verify cleanup completed successfully
2. Check for any orphaned resources
3. Review test metrics (RTO, RPO, etc.)
4. Document any failures or warnings
5. Update runbooks based on test results

## Scheduling Tests

### Manual Testing
Run integration tests:
- Before major deployments
- After infrastructure changes
- Monthly as part of DR drills
- When investigating issues

### Automated Testing
Consider scheduling tests:
- Weekly: Database replication test
- Monthly: Full failover tests
- Quarterly: Security controls test

Example cron schedule:
```bash
# Weekly database replication test (Sundays at 2 AM)
0 2 * * 0 cd /path/to/infrastructure/tests/integration && python test_database_replication.py

# Monthly failover test (First Sunday at 3 AM)
0 3 1-7 * 0 cd /path/to/infrastructure/tests/integration && python test_failover_aws_to_azure.py
```

## Metrics and Reporting

### Key Metrics Tracked
- **RTO (Recovery Time Objective)**: Time from failure to recovery
- **RPO (Recovery Point Objective)**: Data loss window
- **Replication Lag**: Time delay for data replication
- **Test Duration**: Total time to run test
- **Success Rate**: Percentage of tests passed

### Generating Reports
Tests automatically generate reports. To save reports:

```bash
python test_failover_aws_to_azure.py > test_report_$(date +%Y%m%d).log 2>&1
```

### Analyzing Results
Review test reports for:
- RTO/RPO compliance
- Replication lag trends
- Security control effectiveness
- Areas for improvement

## Contributing

When adding new integration tests:
1. Follow the existing test structure
2. Include comprehensive logging
3. Implement proper cleanup
4. Document test purpose and requirements
5. Update this README

## Related Documentation

- [Architecture Documentation](../../docs/ARCHITECTURE.md)
- [Deployment Guide](../../docs/DEPLOYMENT_GUIDE.md)
- [Manual Failover Runbook](../../docs/runbooks/MANUAL_FAILOVER.md)
- [Troubleshooting Guide](../../docs/runbooks/TROUBLESHOOTING.md)

## Support

For issues with integration tests:
1. Check troubleshooting section above
2. Review test logs for specific errors
3. Consult related documentation
4. Contact DevOps team

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2024-01-15 | 1.0 | DevOps Team | Initial version |
