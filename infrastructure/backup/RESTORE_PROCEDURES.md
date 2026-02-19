# Database Backup Restoration Procedures

This document provides step-by-step procedures for restoring database backups across all cloud providers.

## Table of Contents

1. [AWS RDS Restoration](#aws-rds-restoration)
2. [Azure Database Restoration](#azure-database-restoration)
3. [GCP Cloud SQL Restoration](#gcp-cloud-sql-restoration)
4. [Automated Restoration](#automated-restoration)
5. [Verification Steps](#verification-steps)
6. [Troubleshooting](#troubleshooting)

## AWS RDS Restoration

### Restore from Automated Snapshot

**Using AWS Console:**

1. Navigate to RDS Console
2. Select "Snapshots" from the left menu
3. Select the automated snapshot you want to restore
4. Click "Actions" → "Restore snapshot"
5. Configure the new DB instance:
   - DB instance identifier: `singha-loyalty-db-restore-YYYYMMDD`
   - DB instance class: `db.t3.micro`
   - VPC: Select the appropriate VPC
   - Subnet group: Select private subnet group
   - Public accessibility: No
   - VPC security groups: Select database security group
6. Click "Restore DB instance"
7. Wait for instance to become available (typically 10-30 minutes)

**Using AWS CLI:**

```bash
# List available snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier singha-loyalty-db-primary \
  --snapshot-type automated

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier singha-loyalty-db-restore-20260215 \
  --db-snapshot-identifier rds:singha-loyalty-db-primary-2026-02-15-03-00 \
  --db-instance-class db.t3.micro \
  --no-publicly-accessible \
  --vpc-security-group-ids sg-xxxxxxxxx

# Monitor restore progress
aws rds describe-db-instances \
  --db-instance-identifier singha-loyalty-db-restore-20260215 \
  --query 'DBInstances[0].DBInstanceStatus'
```

**Using Python Script:**

```bash
python infrastructure/backup/backup_restore.py \
  --config infrastructure/backup/backup_config.json \
  --cloud AWS \
  --restore-type snapshot \
  --source rds:singha-loyalty-db-primary-2026-02-15-03-00 \
  --target singha-loyalty-db-restore-20260215
```

### Point-in-Time Recovery (PITR)

**Using AWS Console:**

1. Navigate to RDS Console
2. Select the source DB instance
3. Click "Actions" → "Restore to point in time"
4. Select "Custom" and choose the date and time
5. Configure the new DB instance (same as snapshot restore)
6. Click "Restore DB instance"

**Using AWS CLI:**

```bash
# Restore to specific point in time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier singha-loyalty-db-primary \
  --target-db-instance-identifier singha-loyalty-db-pitr-20260215 \
  --restore-time 2026-02-15T10:30:00Z \
  --db-instance-class db.t3.micro \
  --no-publicly-accessible
```

**Using Python Script:**

```bash
python infrastructure/backup/backup_restore.py \
  --config infrastructure/backup/backup_config.json \
  --cloud AWS \
  --restore-type point-in-time \
  --source singha-loyalty-db-primary \
  --target singha-loyalty-db-pitr-20260215 \
  --restore-time 2026-02-15T10:30:00
```

## Azure Database Restoration

### Restore from Backup

**Using Azure Portal:**

1. Navigate to Azure Portal
2. Go to "Azure Database for MySQL servers"
3. Select the source server
4. Click "Restore" in the toolbar
5. Configure restore settings:
   - Server name: `singha-loyalty-mysql-restore-20260215`
   - Restore point: Select date and time
   - Location: Same as source
   - Pricing tier: Same as source
6. Click "OK" to start restore
7. Wait for restore to complete (typically 10-30 minutes)

**Using Azure CLI:**

```bash
# List available restore points
az mysql server show \
  --resource-group singha-loyalty-rg \
  --name singha-loyalty-mysql-azure \
  --query "earliestRestoreDate"

# Restore to point in time
az mysql server restore \
  --resource-group singha-loyalty-rg \
  --name singha-loyalty-mysql-restore-20260215 \
  --restore-point-in-time "2026-02-15T10:30:00Z" \
  --source-server singha-loyalty-mysql-azure

# Monitor restore progress
az mysql server show \
  --resource-group singha-loyalty-rg \
  --name singha-loyalty-mysql-restore-20260215 \
  --query "userVisibleState"
```

**Using Python Script:**

```bash
python infrastructure/backup/backup_restore.py \
  --config infrastructure/backup/backup_config.json \
  --cloud Azure \
  --restore-type point-in-time \
  --source singha-loyalty-mysql-azure \
  --target singha-loyalty-mysql-restore-20260215 \
  --restore-time 2026-02-15T10:30:00
```

## GCP Cloud SQL Restoration

### Restore from Backup

**Using GCP Console:**

1. Navigate to Cloud SQL Console
2. Select the source instance
3. Click "Backups" tab
4. Select the backup you want to restore
5. Click "Restore"
6. Choose restore option:
   - Restore to the same instance (overwrites data)
   - Restore to a new instance (recommended)
7. If creating new instance:
   - Instance ID: `singha-loyalty-mysql-restore-20260215`
   - Configure same settings as source
8. Click "Restore"
9. Wait for restore to complete (typically 10-30 minutes)

**Using gcloud CLI:**

```bash
# List available backups
gcloud sql backups list \
  --instance=singha-loyalty-mysql-gcp \
  --project=your-project-id

# Restore from backup (to new instance)
gcloud sql backups restore BACKUP_ID \
  --backup-instance=singha-loyalty-mysql-gcp \
  --restore-instance=singha-loyalty-mysql-restore-20260215 \
  --project=your-project-id

# Monitor restore progress
gcloud sql operations list \
  --instance=singha-loyalty-mysql-restore-20260215 \
  --project=your-project-id
```

**Using Python Script:**

```bash
python infrastructure/backup/backup_restore.py \
  --config infrastructure/backup/backup_config.json \
  --cloud GCP \
  --restore-type snapshot \
  --source singha-loyalty-mysql-gcp \
  --target singha-loyalty-mysql-restore-20260215 \
  --backup-id 1234567890
```

## Automated Restoration

### Full Automated Restore Test

Run a complete restore test on all clouds:

```bash
# Run restore test
python infrastructure/backup/backup_restore_test.py \
  --config infrastructure/backup/backup_config.json \
  --test-all
```

This will:
1. Identify latest backups on each cloud
2. Restore to test instances
3. Verify data integrity
4. Generate test report
5. Clean up test instances

### Scheduled Monthly Testing

Add to cron for monthly automated testing:

```bash
# Run on the 1st of each month at 2 AM
0 2 1 * * /usr/bin/python3 /path/to/infrastructure/backup/backup_restore_test.py --config /path/to/backup_config.json --test-all
```

## Verification Steps

After any restore operation, perform these verification steps:

### 1. Check Instance Status

**AWS:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier INSTANCE_ID \
  --query 'DBInstances[0].DBInstanceStatus'
```

**Azure:**
```bash
az mysql server show \
  --resource-group RESOURCE_GROUP \
  --name SERVER_NAME \
  --query "userVisibleState"
```

**GCP:**
```bash
gcloud sql instances describe INSTANCE_NAME \
  --project=PROJECT_ID \
  --format="value(state)"
```

### 2. Test Database Connectivity

```bash
# Test MySQL connection
mysql -h ENDPOINT -u admin -p -e "SELECT 1;"
```

### 3. Verify Data Integrity

```bash
# Check table counts
mysql -h ENDPOINT -u admin -p DATABASE_NAME -e "
  SELECT 
    table_name,
    table_rows
  FROM information_schema.tables
  WHERE table_schema = 'DATABASE_NAME'
  ORDER BY table_name;
"

# Check latest records
mysql -h ENDPOINT -u admin -p DATABASE_NAME -e "
  SELECT MAX(created_at) as latest_record FROM customers;
  SELECT MAX(created_at) as latest_record FROM transactions;
"
```

### 4. Compare with Source

```bash
# Run consistency check
python infrastructure/scripts/verify_consistency.py \
  --config infrastructure/backup/backup_config.json \
  --source SOURCE_INSTANCE \
  --target RESTORED_INSTANCE
```

## Troubleshooting

### Restore Takes Too Long

**Symptoms:** Restore operation exceeds 1 hour

**Solutions:**
1. Check instance size - larger databases take longer
2. Verify network connectivity
3. Check cloud provider status page for outages
4. Consider using a larger instance class for faster restore

### Restore Fails with Permission Error

**Symptoms:** "Access Denied" or "Insufficient Permissions"

**Solutions:**
1. Verify IAM roles have restore permissions
2. Check service account credentials
3. Ensure backup is accessible from current account
4. Review security group and network ACL settings

### Restored Instance Not Accessible

**Symptoms:** Cannot connect to restored database

**Solutions:**
1. Verify security group allows inbound traffic on port 3306
2. Check VPC and subnet configuration
3. Ensure instance is in correct VPC
4. Verify DNS resolution
5. Check database user credentials

### Data Missing After Restore

**Symptoms:** Restored database missing recent data

**Solutions:**
1. Verify restore point time is correct
2. Check replication lag at time of backup
3. Ensure backup completed successfully
4. Review backup logs for errors
5. Consider using more recent backup or PITR

### Restore Verification Fails

**Symptoms:** Verification script reports failures

**Solutions:**
1. Wait for instance to fully initialize
2. Check database engine logs
3. Verify all tables are accessible
4. Run manual data integrity checks
5. Compare checksums with source database

## Emergency Restore Procedure

In case of catastrophic failure requiring immediate restore:

### 1. Assess Situation
- Identify which cloud(s) are affected
- Determine data loss window
- Identify latest good backup

### 2. Initiate Restore
```bash
# Use automated script for fastest restore
python infrastructure/backup/backup_restore.py \
  --config infrastructure/backup/backup_config.json \
  --cloud [AWS|Azure|GCP] \
  --restore-type snapshot \
  --source LATEST_BACKUP_ID \
  --target PRODUCTION_INSTANCE_NAME
```

### 3. Monitor Progress
```bash
# Watch restore status
watch -n 30 'python infrastructure/backup/backup_restore.py --status RESTORE_ID'
```

### 4. Verify and Promote
```bash
# Verify restored instance
python infrastructure/backup/backup_verification.py \
  --config infrastructure/backup/backup_config.json \
  --instance RESTORED_INSTANCE

# If verification passes, update DNS to point to restored instance
python infrastructure/scripts/dns_failover.py \
  --target RESTORED_INSTANCE
```

### 5. Post-Restore Actions
- Notify stakeholders of restore completion
- Document incident and restore time
- Review backup procedures
- Update runbooks if needed

## SLA Targets

- **Restore Time Objective (RTO):** < 1 hour
- **Recovery Point Objective (RPO):** < 5 seconds
- **Verification Time:** < 15 minutes
- **Total Recovery Time:** < 75 minutes

## Contact Information

For restore assistance:
- Primary: DevOps Team (devops@example.com)
- Secondary: Database Admin (dba@example.com)
- Emergency: On-call Engineer (oncall@example.com)

## Related Documentation

- [Backup Manager Documentation](./README.md)
- [Failover Procedures](../scripts/README.md)
- [Disaster Recovery Plan](../DEPLOYMENT_CHECKLIST.md)
