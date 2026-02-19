# Database Promotion Runbook

## Purpose
This runbook provides detailed instructions for promoting a database replica to primary status during a failover event.

## When to Use
- During automated or manual failover
- When primary database fails
- For DR drills and testing
- When migrating primary to different cloud

## Prerequisites
- Replica database is healthy and replicating
- Replication lag is acceptable (< 60 seconds)
- Network connectivity verified
- Database admin credentials available

## Important Notes

⚠️ **Critical Considerations**:
- Promoting a replica stops replication permanently
- Data written after promotion won't replicate back automatically
- Promotion is a one-way operation - requires manual reconfiguration to reverse
- Always verify replication lag before promotion to minimize data loss

---

## Promotion Procedure

### Phase 1: Pre-Promotion Checks (2 minutes)

#### Step 1.1: Verify Replica Health

**For AWS RDS**:
```bash
# Check RDS instance status
aws rds describe-db-instances \
  --db-instance-identifier multicloud-dr-rds \
  --query "DBInstances[0].[DBInstanceStatus,ReadReplicaSourceDBInstanceIdentifier]"

# Expected: Status = available, Source = <primary-instance-id>
```

**For Azure Database for MySQL**:
```bash
# Check server status
az mysql server show \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-mysql \
  --query "[provisioningState,replicationRole]"

# Expected: provisioningState = Succeeded, replicationRole = Replica
```

**For GCP Cloud SQL**:
```bash
# Check instance status
gcloud sql instances describe multicloud-dr-cloudsql \
  --format="value(state,replicaConfiguration.kind)"

# Expected: state = RUNNABLE, kind = READ_REPLICA
```

#### Step 1.2: Check Replication Status

**Connect to replica database**:

```bash
# AWS RDS
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier multicloud-dr-rds \
  --query "DBInstances[0].Endpoint.Address" --output text)
mysql -h ${RDS_ENDPOINT} -u admin -p

# Azure MySQL
AZURE_MYSQL=$(az mysql server show \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-mysql \
  --query "fullyQualifiedDomainName" -o tsv)
mysql -h ${AZURE_MYSQL} -u admin@multicloud-dr-mysql -p

# GCP Cloud SQL
gcloud sql connect multicloud-dr-cloudsql --user=root
```

**Check replication status**:

```sql
SHOW SLAVE STATUS\G

-- Key fields to check:
-- Slave_IO_Running: Yes
-- Slave_SQL_Running: Yes
-- Seconds_Behind_Master: <should be low>
-- Last_Error: <should be empty>
```

**Decision Point**:
- ✅ Proceed if: Both threads running, lag < 60 seconds, no errors
- ⚠️ Wait if: Lag > 60 seconds but decreasing
- ❌ Investigate if: Threads not running or errors present

#### Step 1.3: Calculate Potential Data Loss

```sql
-- Get current replication position
SHOW SLAVE STATUS\G

-- Note these values:
-- Master_Log_File: mysql-bin.000123
-- Read_Master_Log_Pos: 456789
-- Exec_Master_Log_Pos: 456789
-- Seconds_Behind_Master: 15

-- Calculate potential data loss window
-- Data Loss Window = Seconds_Behind_Master + Time_To_Promote (typically 30-60 seconds)
```

**Document**: Expected data loss window for incident report

---

### Phase 2: Stop Replication (1 minute)

#### Step 2.1: Stop Slave Threads

```sql
-- Stop replication
STOP SLAVE;

-- Verify stopped
SHOW SLAVE STATUS\G
```

**Expected Output**:
```
Slave_IO_Running: No
Slave_SQL_Running: No
```

#### Step 2.2: Record Final Replication Position

```sql
-- Record final position for documentation
SHOW SLAVE STATUS\G

-- Note these values for incident report:
-- Master_Log_File: <file>
-- Read_Master_Log_Pos: <position>
-- Exec_Master_Log_Pos: <position>
-- Seconds_Behind_Master: <lag>
```

**Save this information** - needed for potential rollback or troubleshooting

---

### Phase 3: Promote to Primary (1 minute)

#### Step 3.1: Reset Slave Configuration

```sql
-- Remove all slave configuration
RESET SLAVE ALL;

-- Verify slave info is cleared
SHOW SLAVE STATUS\G
```

**Expected Output**: Empty set (no slave status)

#### Step 3.2: Disable Read-Only Mode

```sql
-- Check current read-only status
SHOW VARIABLES LIKE 'read_only';
SHOW VARIABLES LIKE 'super_read_only';

-- Disable read-only mode
SET GLOBAL read_only = OFF;
SET GLOBAL super_read_only = OFF;

-- Verify
SHOW VARIABLES LIKE 'read_only';
SHOW VARIABLES LIKE 'super_read_only';
```

**Expected Output**:
```
read_only: OFF
super_read_only: OFF
```

#### Step 3.3: Enable Binary Logging (if not already enabled)

```sql
-- Check binary logging status
SHOW VARIABLES LIKE 'log_bin';

-- If OFF, binary logging needs to be enabled via configuration
-- For AWS RDS: Modify parameter group
-- For Azure: Modify server parameters
-- For GCP: Modify instance flags

-- Verify binary logging is ON
SHOW VARIABLES LIKE 'log_bin';
SHOW MASTER STATUS;
```

**Expected Output**:
```
log_bin: ON
File: mysql-bin.000001
Position: 154
```

---

### Phase 4: Verification (2 minutes)

#### Step 4.1: Test Write Operations

```sql
-- Create test table if not exists
CREATE TABLE IF NOT EXISTS promotion_test (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME,
    test_data VARCHAR(255)
);

-- Insert test data
INSERT INTO promotion_test (timestamp, test_data) 
VALUES (NOW(), 'Promotion test - write successful');

-- Verify insert
SELECT * FROM promotion_test ORDER BY id DESC LIMIT 1;

-- Clean up test data
DELETE FROM promotion_test WHERE test_data LIKE 'Promotion test%';
```

**Expected**: All operations succeed without errors

#### Step 4.2: Verify No Replication Configured

```sql
-- Ensure no slave configuration remains
SHOW SLAVE STATUS\G

-- Should return empty set
```

#### Step 4.3: Check Database Connections

```sql
-- View active connections
SHOW PROCESSLIST;

-- Check for any blocked queries
SELECT * FROM information_schema.processlist 
WHERE state != '' AND time > 10;

-- Verify no replication threads
SELECT * FROM information_schema.processlist 
WHERE user = 'system user';
```

**Expected**: No replication threads, normal application connections

#### Step 4.4: Verify Binary Log Status

```sql
-- Check binary logs are being generated
SHOW MASTER STATUS;

-- List binary logs
SHOW BINARY LOGS;

-- Verify binary log format
SHOW VARIABLES LIKE 'binlog_format';
```

**Expected**: Binary logs present and being written

---

### Phase 5: Post-Promotion Configuration (2 minutes)

#### Step 5.1: Create Replication User (if needed)

```sql
-- Create replication user for future replicas
CREATE USER IF NOT EXISTS 'replication_user'@'%' 
IDENTIFIED BY 'secure-replication-password';

GRANT REPLICATION SLAVE ON *.* TO 'replication_user'@'%';

FLUSH PRIVILEGES;

-- Verify user created
SELECT user, host FROM mysql.user WHERE user = 'replication_user';
```

#### Step 5.2: Update Application Configuration

**Update database endpoint in application**:

```bash
# For AWS (using Secrets Manager)
aws secretsmanager update-secret \
  --secret-id /multicloud-dr/db/endpoint \
  --secret-string "${NEW_PRIMARY_ENDPOINT}"

# For Azure (using Key Vault)
az keyvault secret set \
  --vault-name multicloud-dr-kv \
  --name db-endpoint \
  --value "${NEW_PRIMARY_ENDPOINT}"

# For GCP (using Secret Manager)
echo -n "${NEW_PRIMARY_ENDPOINT}" | \
gcloud secrets versions add db-endpoint --data-file=-
```

#### Step 5.3: Restart Application Instances

```bash
# AWS EC2
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name multicloud-dr-asg

# Azure VMSS
az vmss restart \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-vmss

# GCP Instance Group
gcloud compute instance-groups managed rolling-action restart \
  multicloud-dr-mig \
  --region us-central1
```

**Wait**: 30-60 seconds for instances to restart and reconnect

#### Step 5.4: Verify Application Connectivity

```bash
# Test application can connect to new primary
curl -f https://your-domain.com/health

# Test write operation through application
curl -X POST https://your-domain.com/api/test \
  -H "Content-Type: application/json" \
  -d '{"test":"promotion-verification"}'

# Verify in database
mysql -h ${NEW_PRIMARY_ENDPOINT} -u admin -p -e "
SELECT * FROM appdb.test_table WHERE test='promotion-verification';
"
```

---

### Phase 6: Configure New Replicas (5 minutes)

#### Step 6.1: Get Binary Log Position

```sql
-- On newly promoted primary
SHOW MASTER STATUS;

-- Note:
-- File: mysql-bin.000001
-- Position: 12345
```

#### Step 6.2: Configure Other Clouds as Replicas

**For each remaining cloud, configure as replica**:

```bash
# Connect to replica database
mysql -h ${REPLICA_ENDPOINT} -u admin -p

# Configure replication from new primary
CHANGE MASTER TO
  MASTER_HOST='${NEW_PRIMARY_ENDPOINT}',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='secure-replication-password',
  MASTER_LOG_FILE='mysql-bin.000001',
  MASTER_LOG_POS=12345;

# Start replication
START SLAVE;

# Verify replication
SHOW SLAVE STATUS\G
```

**Expected**:
- Slave_IO_Running: Yes
- Slave_SQL_Running: Yes
- Seconds_Behind_Master: 0 (or low)

---

## Cloud-Specific Procedures

### AWS RDS Promotion

**Using AWS Console**:
1. Navigate to RDS Console
2. Select the read replica
3. Click "Actions" → "Promote read replica"
4. Confirm promotion
5. Wait for status to change to "available"

**Using AWS CLI**:
```bash
# Promote read replica
aws rds promote-read-replica \
  --db-instance-identifier multicloud-dr-rds

# Monitor promotion status
aws rds describe-db-instances \
  --db-instance-identifier multicloud-dr-rds \
  --query "DBInstances[0].DBInstanceStatus"

# Wait for status: available
```

**Note**: AWS RDS promotion is automatic and handles most steps internally

### Azure Database Promotion

**Using Azure Portal**:
1. Navigate to Azure Database for MySQL
2. Select the replica server
3. Click "Replication" → "Stop replication"
4. Confirm to promote to standalone server

**Using Azure CLI**:
```bash
# Stop replication (promotes to standalone)
az mysql server replica stop \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-mysql

# Verify status
az mysql server show \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-mysql \
  --query "replicationRole"

# Expected: None (standalone server)
```

### GCP Cloud SQL Promotion

**Using GCP Console**:
1. Navigate to Cloud SQL Instances
2. Select the replica instance
3. Click "Promote" button
4. Confirm promotion

**Using gcloud CLI**:
```bash
# Promote replica
gcloud sql instances promote-replica multicloud-dr-cloudsql

# Monitor operation
gcloud sql operations list \
  --instance=multicloud-dr-cloudsql \
  --limit=1

# Verify status
gcloud sql instances describe multicloud-dr-cloudsql \
  --format="value(replicaConfiguration.kind)"

# Expected: null (no longer a replica)
```

---

## Rollback Procedure

If promotion fails or needs to be reversed:

### Step 1: Stop Application Writes

```sql
-- On promoted database
SET GLOBAL read_only = ON;
SET GLOBAL super_read_only = ON;
```

### Step 2: Reconfigure as Replica

```sql
-- Get original primary's binary log position
-- (from pre-promotion documentation)

CHANGE MASTER TO
  MASTER_HOST='${ORIGINAL_PRIMARY}',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='replication-password',
  MASTER_LOG_FILE='${ORIGINAL_LOG_FILE}',
  MASTER_LOG_POS=${ORIGINAL_LOG_POS};

START SLAVE;

SHOW SLAVE STATUS\G
```

### Step 3: Revert Application Configuration

```bash
# Update application to use original primary
aws secretsmanager update-secret \
  --secret-id /multicloud-dr/db/endpoint \
  --secret-string "${ORIGINAL_PRIMARY_ENDPOINT}"

# Restart application
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name multicloud-dr-asg
```

---

## Success Criteria

Promotion is successful when:

- ✅ Replication stopped cleanly
- ✅ Read-only mode disabled
- ✅ Write operations succeed
- ✅ Binary logging enabled and working
- ✅ Application connected to new primary
- ✅ No errors in database logs
- ✅ Other clouds configured as replicas

## Common Issues

### Issue 1: Cannot Disable Read-Only Mode

**Symptom**: `SET GLOBAL read_only = OFF` fails

**Solution**:
```sql
-- Check for active connections holding locks
SHOW PROCESSLIST;

-- Kill blocking connections
KILL <connection_id>;

-- Check for super_read_only
SET GLOBAL super_read_only = OFF;
SET GLOBAL read_only = OFF;
```

### Issue 2: Replication Won't Stop

**Symptom**: `STOP SLAVE` hangs or fails

**Solution**:
```sql
-- Check for long-running transactions
SELECT * FROM information_schema.processlist 
WHERE user = 'system user';

-- Force stop (use with caution)
STOP SLAVE IO_THREAD;
STOP SLAVE SQL_THREAD;

-- If still hanging, restart database (last resort)
```

### Issue 3: Binary Logging Not Enabled

**Symptom**: `SHOW MASTER STATUS` returns empty

**Solution**:
```bash
# Binary logging requires database restart
# Update configuration first

# AWS RDS: Modify parameter group
aws rds modify-db-parameter-group \
  --db-parameter-group-name multicloud-dr-params \
  --parameters "ParameterName=log_bin,ParameterValue=1,ApplyMethod=pending-reboot"

# Reboot instance
aws rds reboot-db-instance --db-instance-identifier multicloud-dr-rds

# Azure: Modify server parameters
az mysql server configuration set \
  --resource-group multicloud-dr-rg \
  --server-name multicloud-dr-mysql \
  --name log_bin \
  --value ON

# GCP: Modify instance flags
gcloud sql instances patch multicloud-dr-cloudsql \
  --database-flags log_bin=on

# Restart required
gcloud sql instances restart multicloud-dr-cloudsql
```

### Issue 4: Application Can't Connect After Promotion

**Symptom**: Connection errors in application logs

**Solution**:
```bash
# Verify endpoint is correct
echo ${NEW_PRIMARY_ENDPOINT}

# Test connection from application server
mysql -h ${NEW_PRIMARY_ENDPOINT} -u admin -p

# Check security groups/firewall rules
# Ensure application can reach new primary

# Verify secrets are updated
aws secretsmanager get-secret-value \
  --secret-id /multicloud-dr/db/endpoint

# Restart application if needed
```

## Monitoring After Promotion

Monitor these metrics for 24 hours after promotion:

- Database CPU and memory utilization
- Connection count
- Query performance
- Replication lag on new replicas
- Application error rates
- Response times

## Documentation Requirements

After promotion, document:

- Timestamp of promotion
- Reason for promotion
- Replication lag at time of promotion
- Estimated data loss window
- Any issues encountered
- Time to complete promotion
- Verification results

## Contact Information

- **Database Admin**: [Phone/Email]
- **On-Call Engineer**: [Phone/Pager]
- **Cloud Architect**: [Phone/Email]

## Related Runbooks

- [MANUAL_FAILOVER.md](MANUAL_FAILOVER.md) - Complete failover procedure
- [FAILBACK.md](FAILBACK.md) - Returning to original primary
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2024-01-15 | 1.0 | DevOps Team | Initial version |
