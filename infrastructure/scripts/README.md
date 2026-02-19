# Database Replication Scripts

This directory contains Python scripts for managing cross-cloud database replication.

## Scripts

### setup_replication.py

Configures binary log replication from AWS RDS MySQL to Azure Database for MySQL and Google Cloud SQL.

**Features:**
- Configures AWS RDS as primary with binary logging
- Creates replication user on primary
- Sets up Azure MySQL as read replica
- Sets up GCP Cloud SQL as read replica
- Monitors replication lag

**Usage:**

```bash
# Set environment variables
export AWS_REGION="us-east-1"
export AWS_DB_IDENTIFIER="singha-loyalty-prod-mysql"
export AWS_MASTER_USERNAME="admin"
export AWS_SECRET_NAME="singha-loyalty-prod-db-credentials"

export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="singha-loyalty-prod-rg"
export AZURE_SERVER_NAME="singha-loyalty-prod-mysql"
export AZURE_ADMIN_USERNAME="azureadmin"
export AZURE_KEY_VAULT_URL="https://singha-loyalty-prod-kv.vault.azure.net/"
export AZURE_SECRET_NAME="mysql-password"

export GCP_PROJECT_ID="your-project-id"
export GCP_INSTANCE_NAME="singha-loyalty-prod-mysql"
export GCP_ROOT_USERNAME="root"
export GCP_SECRET_NAME="singha-loyalty-prod-mysql-password"

export REPLICATION_USERNAME="repl_user"
export REPLICATION_PASSWORD="secure_password_here"

# Run the script
python setup_replication.py
```

**Output:**
```
REPLICATION SETUP SUMMARY
============================================================
AWS Primary: rds-endpoint.amazonaws.com:3306
Azure Replica: mysql-server.mysql.database.azure.com
GCP Replica: 35.123.45.67

Replication Lag:
  Azure: 0.5 seconds
  GCP: 0.3 seconds
============================================================
```

### verify_consistency.py

Verifies data consistency across AWS, Azure, and GCP MySQL databases.

**Features:**
- Compares row counts for all tables
- Computes and compares checksums for table data
- Identifies discrepancies between primary and replicas
- Logs inconsistencies for investigation
- Generates consistency reports

**Usage:**

```bash
# Set environment variables (same as setup_replication.py)
export DATABASE_NAME="singha_loyalty"
export AWS_REGION="us-east-1"
# ... (other environment variables)

# Run the script
python verify_consistency.py
```

**Output:**
```
DATABASE CONSISTENCY REPORT
================================================================================
Timestamp: 2024-02-15 10:30:00
Status: ✓ CONSISTENT

Tables Checked:
  AWS: 5 tables
  Azure: 5 tables
  GCP: 5 tables

✓ All databases are consistent!

Table Details:

  Table: customers
    AWS:   1,234 rows, checksum=a1b2c3d4...
    Azure: 1,234 rows, checksum=a1b2c3d4...
    GCP:   1,234 rows, checksum=a1b2c3d4...

  Table: transactions
    AWS:   5,678 rows, checksum=e5f6g7h8...
    Azure: 5,678 rows, checksum=e5f6g7h8...
    GCP:   5,678 rows, checksum=e5f6g7h8...
================================================================================
```

## Requirements

Install Python dependencies:

```bash
pip install -r ../requirements.txt
```

Required packages:
- boto3 (AWS SDK)
- pymysql (MySQL connector)
- azure-identity (Azure authentication)
- azure-mgmt-rdbms (Azure MySQL management)
- azure-keyvault-secrets (Azure Key Vault)
- google-cloud-sql (GCP Cloud SQL)
- google-cloud-secret-manager (GCP Secret Manager)

## Prerequisites

### AWS Setup
1. RDS MySQL 8.0 instance with binary logging enabled
2. AWS credentials configured (`aws configure`)
3. Secrets Manager secret with database credentials
4. IAM permissions for RDS and Secrets Manager

### Azure Setup
1. Azure Database for MySQL Flexible Server
2. Azure credentials configured (`az login`)
3. Key Vault with database credentials
4. Network connectivity to AWS RDS (VPN or public endpoint)

### GCP Setup
1. Cloud SQL MySQL instance
2. GCP credentials configured (`gcloud auth login`)
3. Secret Manager with database credentials
4. Network connectivity to AWS RDS (VPN or public endpoint)

## Network Connectivity

For cross-cloud replication to work, you need network connectivity between clouds:

**Option 1: Public Endpoints (Simpler, Less Secure)**
- Enable public IP on all database instances
- Configure firewall rules to allow traffic between clouds
- Use SSL/TLS for encryption

**Option 2: VPN/Private Connectivity (More Secure)**
- Set up VPN between AWS VPC, Azure VNet, and GCP VPC
- Use private IP addresses for replication
- Configure routing tables

**Option 3: Cloud Interconnect (Production)**
- AWS Direct Connect + Azure ExpressRoute + GCP Cloud Interconnect
- Dedicated private connections
- Best performance and security

## Monitoring

### Replication Lag

Monitor replication lag continuously:

```bash
# Run monitoring in a loop
while true; do
    python setup_replication.py 2>&1 | grep "Replication Lag"
    sleep 60
done
```

### Consistency Checks

Run consistency checks regularly:

```bash
# Add to cron for hourly checks
0 * * * * cd /path/to/infrastructure/scripts && python verify_consistency.py >> consistency.log 2>&1
```

## Troubleshooting

### Replication Not Starting

**Issue**: Replica shows "Replica IO Running: No"

**Solutions:**
1. Check network connectivity between clouds
2. Verify replication user credentials
3. Check firewall rules allow MySQL port (3306)
4. Verify binary logging is enabled on primary
5. Check master log file and position are correct

### High Replication Lag

**Issue**: Replication lag > 5 seconds

**Solutions:**
1. Check network bandwidth between clouds
2. Verify replica instance has sufficient resources
3. Check for long-running queries on primary
4. Consider increasing replica instance size
5. Check for replication errors in MySQL logs

### Consistency Mismatches

**Issue**: Checksums don't match between databases

**Solutions:**
1. Check replication status on replicas
2. Verify replication lag is low
3. Check for replication errors
4. Consider re-initializing replica from primary backup
5. Check for manual writes to replica (should be read-only)

## Security Best Practices

1. **Never hardcode credentials** - Always use secret managers
2. **Use SSL/TLS** - Enable SSL for all database connections
3. **Rotate credentials** - Rotate replication user password every 90 days
4. **Least privilege** - Grant only necessary permissions to replication user
5. **Audit logs** - Enable audit logging on all databases
6. **Network isolation** - Use private connectivity when possible

## Testing

Property-based tests for replication are in `../tests/property/`:
- `test_replication_lag.py` - Tests replication lag bounds (< 5 seconds)
- `test_consistency_verification.py` - Tests consistency check frequency

Run tests:

```bash
cd ../tests/property
pytest test_replication_lag.py -v
pytest test_consistency_verification.py -v
```

## Next Steps

After setting up replication:

1. **Verify replication is working**
   ```bash
   python verify_consistency.py
   ```

2. **Monitor replication lag**
   - Set up CloudWatch/Azure Monitor/Cloud Monitoring alerts
   - Alert if lag > 5 seconds

3. **Test failover**
   - Simulate primary failure
   - Promote replica to primary
   - Verify application can connect to new primary

4. **Set up automated monitoring**
   - Deploy health monitor service (Task 8)
   - Configure alerting (Task 8.2)

5. **Proceed to Task 7**
   - DNS and traffic routing setup
   - Route 53 health checks
   - Failover orchestration
