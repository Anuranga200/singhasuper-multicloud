# Backup and Recovery Module

This module provides comprehensive backup and recovery capabilities for the Multi-Cloud Disaster Recovery System across AWS, Azure, and GCP.

## Overview

The backup module ensures data protection and recovery capabilities through:
- Automated daily backups on all cloud providers
- 30-day backup retention with point-in-time recovery
- Backup integrity verification
- Automated restore testing
- Geographic backup separation

## Components

### 1. Backup Manager (`backup_manager.py`)

Manages automated database backups across all clouds.

**Features:**
- Configure automated daily backups
- 30-day retention period enforcement
- Point-in-time recovery (7 days)
- Geographic separation verification
- Backup reporting

**Usage:**

```bash
# Configure backups on all clouds
python backup_manager.py \
  --config backup_config.json \
  --action configure

# List all backups
python backup_manager.py \
  --config backup_config.json \
  --action list

# Verify geographic separation
python backup_manager.py \
  --config backup_config.json \
  --action verify

# Generate backup report
python backup_manager.py \
  --config backup_config.json \
  --action report
```

### 2. Backup Verification (`backup_verification.py`)

Verifies backup integrity after each backup completes.

**Features:**
- Verify backup existence and accessibility
- Check backup status and metadata
- Validate backup size and encryption
- Alert on verification failures
- Log verification results

**Usage:**

```bash
# Verify latest backups from all clouds
python backup_verification.py \
  --config backup_config.json

# Verify specific AWS backup
python backup_verification.py \
  --config backup_config.json \
  --cloud AWS \
  --backup-id rds:singha-loyalty-db-primary-2026-02-15-03-00
```

### 3. Backup Restore (`backup_restore.py`)

Handles backup restoration operations.

**Features:**
- Restore from automated snapshots
- Point-in-time recovery
- Restore to new or existing instances
- Verify restoration success
- Track restore duration

**Usage:**

```bash
# Restore AWS from snapshot
python backup_restore.py \
  --config backup_config.json \
  --cloud AWS \
  --restore-type snapshot \
  --source rds:singha-loyalty-db-primary-2026-02-15-03-00 \
  --target singha-loyalty-db-restore-20260215

# Restore AWS to point in time
python backup_restore.py \
  --config backup_config.json \
  --cloud AWS \
  --restore-type point-in-time \
  --source singha-loyalty-db-primary \
  --target singha-loyalty-db-pitr-20260215 \
  --restore-time 2026-02-15T10:30:00

# Restore Azure
python backup_restore.py \
  --config backup_config.json \
  --cloud Azure \
  --restore-type point-in-time \
  --source singha-loyalty-mysql-azure \
  --target singha-loyalty-mysql-restore-20260215 \
  --restore-time 2026-02-15T10:30:00

# Restore GCP
python backup_restore.py \
  --config backup_config.json \
  --cloud GCP \
  --restore-type snapshot \
  --source singha-loyalty-mysql-gcp \
  --target singha-loyalty-mysql-restore-20260215 \
  --backup-id 1234567890
```

### 4. Backup Restore Testing (`backup_restore_test.py`)

Performs automated monthly backup restoration tests.

**Features:**
- Automated monthly restore testing
- Restore to isolated test environment
- Data integrity verification
- Test result logging and reporting
- Automatic cleanup of test resources

**Usage:**

```bash
# Test all cloud providers
python backup_restore_test.py \
  --config backup_config.json \
  --test-all \
  --output backup_test_report.json

# Test specific cloud
python backup_restore_test.py \
  --config backup_config.json \
  --cloud AWS \
  --output aws_test_report.json
```

**Scheduled Testing:**

Add to cron for monthly automated testing:

```bash
# Run on the 1st of each month at 2 AM
0 2 1 * * /usr/bin/python3 /path/to/infrastructure/backup/backup_restore_test.py --config /path/to/backup_config.json --test-all
```

## Configuration

Create a configuration file based on `backup_config.example.json`:

```json
{
  "aws_region": "us-east-1",
  "aws_db_instance_id": "singha-loyalty-db-primary",
  
  "azure_subscription_id": "your-azure-subscription-id",
  "azure_resource_group": "singha-loyalty-rg",
  "azure_server_name": "singha-loyalty-mysql-azure",
  
  "gcp_project_id": "your-gcp-project-id",
  "gcp_instance_name": "singha-loyalty-mysql-gcp",
  "gcp_credentials_file": "/path/to/service-account-key.json",
  
  "backup_retention_days": 30,
  "point_in_time_recovery_days": 7,
  "backup_window": "03:00-04:00",
  
  "alert_email": "admin@example.com",
  "alert_sms": "+1234567890"
}
```

## Backup Schedule

### AWS RDS
- **Backup Window:** 03:00-04:00 UTC daily
- **Retention:** 30 days
- **Point-in-Time Recovery:** 7 days
- **Storage:** S3 in same region, different AZ

### Azure Database for MySQL
- **Backup Window:** Automatic (managed by Azure)
- **Retention:** 30 days
- **Point-in-Time Recovery:** 7 days
- **Storage:** Geo-redundant (paired region)

### GCP Cloud SQL
- **Backup Window:** 03:00 UTC daily
- **Retention:** 30 backups
- **Point-in-Time Recovery:** 7 days
- **Storage:** Multi-region

## Backup Verification

Verification checks performed after each backup:

1. **Backup Existence:** Verify backup exists in cloud provider
2. **Backup Status:** Check backup status is 'available' or 'completed'
3. **Backup Size:** Validate backup size is reasonable
4. **Backup Encryption:** Verify encryption is enabled
5. **Backup Age:** Check backup is recent

## Restore Procedures

See [RESTORE_PROCEDURES.md](./RESTORE_PROCEDURES.md) for detailed manual restoration procedures.

### Restore SLA

- **Recovery Time Objective (RTO):** < 1 hour
- **Recovery Point Objective (RPO):** < 5 seconds
- **Verification Time:** < 15 minutes
- **Total Recovery Time:** < 75 minutes

## Testing

### Property-Based Tests

Located in `infrastructure/tests/property/test_backup.py`:

- **Property 34:** Daily Backup Execution
- **Property 35:** Backup Retention Period
- **Property 36:** Point-in-Time Recovery Window
- **Property 37:** Backup Integrity Verification
- **Property 38:** Backup Geographic Separation
- **Property 39:** Backup Restore Time
- **Property 40:** Monthly Restore Testing

Run tests:

```bash
cd infrastructure
pytest tests/property/test_backup.py -v
```

### Monthly Restore Testing

Automated restore tests verify:
1. Backups can be restored successfully
2. Restore completes within SLA (1 hour)
3. Data integrity is maintained
4. Test resources are cleaned up

## Monitoring and Alerts

### Backup Monitoring

Monitor these metrics:
- Daily backup completion rate
- Backup size trends
- Backup duration
- Verification success rate
- Geographic separation status

### Alerts

Alerts are sent for:
- Backup failures
- Verification failures
- Restore test failures
- Retention policy violations
- Geographic separation issues

## Troubleshooting

### Backup Failures

**Symptoms:** Backup does not complete successfully

**Solutions:**
1. Check database instance status
2. Verify IAM permissions
3. Check storage quota
4. Review database logs
5. Verify network connectivity

### Verification Failures

**Symptoms:** Backup verification reports failures

**Solutions:**
1. Check backup status in cloud console
2. Verify backup size is reasonable
3. Check encryption settings
4. Review verification logs
5. Manually verify backup accessibility

### Restore Failures

**Symptoms:** Restore operation fails or times out

**Solutions:**
1. Verify backup exists and is accessible
2. Check target instance configuration
3. Verify IAM permissions
4. Check network and security group settings
5. Review restore logs for errors

See [RESTORE_PROCEDURES.md](./RESTORE_PROCEDURES.md) for detailed troubleshooting.

## Dependencies

```bash
pip install boto3 azure-identity azure-mgmt-rdbms google-cloud-sql pytest hypothesis
```

## Security Considerations

1. **Credentials:** Store cloud credentials securely (environment variables, secret managers)
2. **Encryption:** All backups are encrypted at rest
3. **Access Control:** Use least privilege IAM policies
4. **Network Security:** Backups stored in private storage
5. **Audit Logging:** All backup operations are logged

## Compliance

The backup module helps meet compliance requirements:

- **Data Protection:** 30-day retention with PITR
- **Business Continuity:** Automated backups and restore testing
- **Disaster Recovery:** Geographic separation and multi-cloud backups
- **Audit Trail:** Comprehensive logging of all operations

## Related Documentation

- [Restore Procedures](./RESTORE_PROCEDURES.md) - Detailed restoration procedures
- [Deployment Checklist](../DEPLOYMENT_CHECKLIST.md) - Deployment verification
- [Verification Guide](../VERIFICATION_GUIDE.md) - System verification
- [Implementation Guide](../IMPLEMENTATION_GUIDE.md) - Implementation details

## Support

For backup and recovery assistance:
- Primary: DevOps Team (devops@example.com)
- Secondary: Database Admin (dba@example.com)
- Emergency: On-call Engineer (oncall@example.com)
