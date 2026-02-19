# Manual Failover Runbook

## Purpose
This runbook provides step-by-step instructions for performing a manual failover from one cloud provider to another in the multi-cloud DR system.

## When to Use
- Planned maintenance on primary cloud
- Performance degradation on primary cloud
- Testing DR procedures
- Compliance requirements for DR drills
- Automated failover has failed

## Prerequisites
- Access to AWS, Azure, and GCP consoles
- AWS CLI, Azure CLI, and gcloud CLI configured
- Database admin credentials
- Route 53 access
- Notification system access

## Severity Levels
- **P1 (Critical)**: Complete primary cloud outage - Execute immediately
- **P2 (High)**: Degraded performance - Execute within 15 minutes
- **P3 (Medium)**: Planned maintenance - Schedule and execute
- **P4 (Low)**: DR drill - Schedule and execute with team

---

## Failover Procedure

### Phase 1: Pre-Failover Assessment (5 minutes)

#### Step 1.1: Verify Current State

```bash
# Check current active cloud
dig your-domain.com +short

# Check health status of all clouds
python scripts/health_monitor.py --status

# Check replication lag
python scripts/setup_replication.py --check-lag
```

**Expected Output**:
- Current DNS points to AWS (or current primary)
- Target cloud (Azure or GCP) shows healthy
- Replication lag < 30 seconds

**Decision Point**: If replication lag > 60 seconds, wait or accept data loss

#### Step 1.2: Notify Stakeholders

```bash
# Send notification
python scripts/failover_orchestrator.py --notify \
  --message "Manual failover initiated to [TARGET_CLOUD]" \
  --severity [P1|P2|P3|P4]
```

**Notify**:
- Operations team
- Development team
- Management (for P1/P2)
- Customers (for P1 with >5 min downtime)

#### Step 1.3: Document Failover

Create incident ticket with:
- Timestamp of failover initiation
- Reason for failover
- Current system state
- Expected downtime
- Assigned personnel

---

### Phase 2: Target Cloud Verification (3 minutes)

#### Step 2.1: Verify Target Cloud Health

**For Azure Failover**:
```bash
# Check Azure VM health
az vmss list-instances \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-vmss \
  --query "[].{Name:name, State:provisioningState, Health:instanceView.statuses[?code=='PowerState/running']}"

# Check Azure Load Balancer
az network lb show \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-lb \
  --query "provisioningState"

# Test application endpoint
AZURE_LB_IP=$(az network public-ip show \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-lb-ip \
  --query "ipAddress" -o tsv)

curl -f https://${AZURE_LB_IP}/health || echo "Health check failed"
```

**For GCP Failover**:
```bash
# Check GCP instance group health
gcloud compute instance-groups managed list-instances \
  multicloud-dr-mig \
  --region us-central1

# Check GCP Load Balancer
gcloud compute forwarding-rules describe multicloud-dr-lb \
  --global

# Test application endpoint
GCP_LB_IP=$(gcloud compute forwarding-rules describe multicloud-dr-lb \
  --global --format="value(IPAddress)")

curl -f https://${GCP_LB_IP}/health || echo "Health check failed"
```

**Go/No-Go Decision**:
- ✅ GO: All health checks pass
- ❌ NO-GO: Health checks fail - investigate before proceeding

#### Step 2.2: Verify Database Replica Health

**For Azure**:
```bash
# Connect to Azure MySQL
AZURE_MYSQL_SERVER=$(az mysql server show \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-mysql \
  --query "fullyQualifiedDomainName" -o tsv)

# Check replication status
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master"
```

**Expected**:
- Slave_IO_Running: Yes
- Slave_SQL_Running: Yes
- Seconds_Behind_Master: < 30

**For GCP**:
```bash
# Check Cloud SQL replication
gcloud sql operations list \
  --instance=multicloud-dr-cloudsql \
  --limit=5

# Connect and check status
gcloud sql connect multicloud-dr-cloudsql --user=root

# In MySQL prompt:
SHOW SLAVE STATUS\G
```

**Expected**:
- Slave_IO_Running: Yes
- Slave_SQL_Running: Yes
- Seconds_Behind_Master: < 30

---

### Phase 3: Database Promotion (2 minutes)

#### Step 3.1: Stop Replication

**For Azure**:
```bash
# Connect to Azure MySQL
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p

# Stop replication
STOP SLAVE;

# Verify stopped
SHOW SLAVE STATUS\G
```

**For GCP**:
```bash
# Connect to Cloud SQL
gcloud sql connect multicloud-dr-cloudsql --user=root

# Stop replication
STOP SLAVE;

# Verify stopped
SHOW SLAVE STATUS\G
```

**Verification**: Slave_IO_Running: No, Slave_SQL_Running: No

#### Step 3.2: Promote Replica to Primary

**For Azure**:
```bash
# Reset slave configuration
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p -e "RESET SLAVE ALL;"

# Verify read-write mode
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p -e "SHOW VARIABLES LIKE 'read_only';"

# If read_only = ON, disable it
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p -e "SET GLOBAL read_only = OFF;"

# Test write operation
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p -e "
USE appdb;
INSERT INTO failover_log (timestamp, event, cloud) VALUES (NOW(), 'Promoted to primary', 'Azure');
"
```

**For GCP**:
```bash
# Reset slave configuration
gcloud sql connect multicloud-dr-cloudsql --user=root

# In MySQL prompt:
RESET SLAVE ALL;

# Verify read-write mode
SHOW VARIABLES LIKE 'read_only';

# If read_only = ON, disable it
SET GLOBAL read_only = OFF;

# Test write operation
USE appdb;
INSERT INTO failover_log (timestamp, event, cloud) VALUES (NOW(), 'Promoted to primary', 'GCP');
```

**Verification**: Write operation succeeds

#### Step 3.3: Update Application Configuration

**For Azure**:
```bash
# Update database endpoint in application
# This is typically done via environment variables or config files

# If using Azure Key Vault
az keyvault secret set \
  --vault-name multicloud-dr-kv \
  --name db-endpoint \
  --value "${AZURE_MYSQL_SERVER}"

# Restart application instances to pick up new config
az vmss restart \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-vmss
```

**For GCP**:
```bash
# Update database endpoint
GCP_SQL_IP=$(gcloud sql instances describe multicloud-dr-cloudsql \
  --format="value(ipAddresses[0].ipAddress)")

# Update secret
echo -n "${GCP_SQL_IP}" | gcloud secrets versions add db-endpoint --data-file=-

# Restart application instances
gcloud compute instance-groups managed rolling-action restart \
  multicloud-dr-mig \
  --region us-central1
```

**Wait**: 30-60 seconds for instances to restart

---

### Phase 4: DNS Update (1 minute)

#### Step 4.1: Update Route 53 Records

**For Azure Failover**:
```bash
# Get Azure Load Balancer IP
AZURE_LB_IP=$(az network public-ip show \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-lb-ip \
  --query "ipAddress" -o tsv)

# Update Route 53 record
aws route53 change-resource-record-sets \
  --hosted-zone-id <HOSTED_ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "your-domain.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "'${AZURE_LB_IP}'"}]
      }
    }]
  }'
```

**For GCP Failover**:
```bash
# Get GCP Load Balancer IP
GCP_LB_IP=$(gcloud compute forwarding-rules describe multicloud-dr-lb \
  --global --format="value(IPAddress)")

# Update Route 53 record
aws route53 change-resource-record-sets \
  --hosted-zone-id <HOSTED_ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "your-domain.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "'${GCP_LB_IP}'"}]
      }
    }]
  }'
```

#### Step 4.2: Verify DNS Propagation

```bash
# Check DNS resolution
dig your-domain.com +short

# Test from multiple locations
curl https://www.whatsmydns.net/api/query?server=8.8.8.8&query=your-domain.com&type=A

# Wait for TTL expiration (60 seconds)
sleep 60

# Verify again
dig your-domain.com +short
```

**Expected**: DNS resolves to new cloud IP

---

### Phase 5: Verification (2 minutes)

#### Step 5.1: Test Application Functionality

```bash
# Test health endpoint
curl -f https://your-domain.com/health

# Test read operation
curl -f https://your-domain.com/api/customers

# Test write operation
curl -X POST https://your-domain.com/api/customers \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Failover Test"}'

# Verify data in database
mysql -h ${NEW_PRIMARY_ENDPOINT} -u admin -p -e "
SELECT * FROM appdb.customers WHERE email='test@example.com';
"
```

**Expected**: All operations succeed

#### Step 5.2: Monitor System Metrics

```bash
# Check application metrics
python monitoring/unified_dashboard.py --check

# Monitor for errors
# AWS CloudWatch (if monitoring from AWS)
aws logs tail /aws/ec2/multicloud-dr --follow

# Azure Monitor
az monitor metrics list \
  --resource <resource-id> \
  --metric "Percentage CPU"

# GCP Cloud Monitoring
gcloud logging read "resource.type=gce_instance" --limit 50
```

**Monitor for**: Error rates, response times, database connections

#### Step 5.3: Verify Replication Stopped on Old Primary

```bash
# If AWS was primary, verify it's no longer replicating
# This prevents split-brain scenarios

# Check AWS RDS
aws rds describe-db-instances \
  --db-instance-identifier multicloud-dr-rds \
  --query "DBInstances[0].DBInstanceStatus"
```

---

### Phase 6: Post-Failover Actions (5 minutes)

#### Step 6.1: Update Monitoring

```bash
# Update monitoring to reflect new primary
python scripts/failover_orchestrator.py --update-monitoring \
  --primary-cloud [azure|gcp]

# Verify alerts are configured for new primary
python monitoring/unified_dashboard.py --verify-alerts
```

#### Step 6.2: Document Failover

Update incident ticket with:
- Actual failover completion time
- RTO achieved (target: 5 minutes)
- RPO achieved (target: 1 minute)
- Any issues encountered
- Data loss (if any)

```bash
# Calculate RTO
echo "Failover started: <START_TIME>"
echo "Failover completed: $(date)"
echo "RTO: <CALCULATED_MINUTES> minutes"

# Calculate RPO
python scripts/verify_consistency.py --check-data-loss
```

#### Step 6.3: Notify Stakeholders

```bash
# Send completion notification
python scripts/failover_orchestrator.py --notify \
  --message "Failover to [TARGET_CLOUD] completed successfully. RTO: X minutes, RPO: Y seconds" \
  --severity resolved
```

**Notify**:
- Operations team
- Development team
- Management
- Customers (if notified of incident)

#### Step 6.4: Schedule Failback (if applicable)

If this was a planned failover or the original primary is restored:

```bash
# Schedule failback
# See FAILBACK.md runbook for detailed steps

# Typical failback timeline:
# - Immediate: For DR drills
# - 24-48 hours: For unplanned outages (allow time to verify stability)
# - Scheduled: For planned maintenance
```

---

## Rollback Procedure

If failover fails or causes issues:

### Step 1: Revert DNS

```bash
# Get original primary IP
ORIGINAL_IP="<original-primary-ip>"

# Revert Route 53 record
aws route53 change-resource-record-sets \
  --hosted-zone-id <HOSTED_ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "your-domain.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "'${ORIGINAL_IP}'"}]
      }
    }]
  }'
```

### Step 2: Demote New Primary

```bash
# Reconnect as replica
# See database replication setup in DEPLOYMENT_GUIDE.md

# Stop writes
SET GLOBAL read_only = ON;

# Reconfigure replication
CHANGE MASTER TO ...
START SLAVE;
```

### Step 3: Notify and Document

```bash
# Notify of rollback
python scripts/failover_orchestrator.py --notify \
  --message "Failover rolled back to original primary" \
  --severity high

# Document rollback reason
```

---

## Success Criteria

Failover is considered successful when:

- ✅ DNS resolves to new cloud
- ✅ Application health checks pass
- ✅ Read operations succeed
- ✅ Write operations succeed
- ✅ No error spikes in logs
- ✅ RTO < 5 minutes
- ✅ RPO < 1 minute
- ✅ Stakeholders notified

## Common Issues

### Issue 1: Replication Lag Too High

**Symptom**: Seconds_Behind_Master > 60

**Solution**:
- Wait for replication to catch up
- If urgent, accept data loss and proceed
- Document data loss window

### Issue 2: Database Promotion Fails

**Symptom**: Cannot disable read_only mode

**Solution**:
```bash
# Check for active connections
SHOW PROCESSLIST;

# Kill blocking connections
KILL <connection_id>;

# Retry promotion
SET GLOBAL read_only = OFF;
```

### Issue 3: DNS Not Propagating

**Symptom**: DNS still resolves to old IP after 5 minutes

**Solution**:
```bash
# Check Route 53 change status
aws route53 get-change --id <change-id>

# Flush local DNS cache
# Linux: sudo systemd-resolve --flush-caches
# Mac: sudo dscacheutil -flushcache
# Windows: ipconfig /flushdns

# Use direct IP if urgent
curl -H "Host: your-domain.com" https://<new-ip>/health
```

### Issue 4: Application Can't Connect to New Database

**Symptom**: Database connection errors in logs

**Solution**:
```bash
# Verify security groups/firewall rules
# Ensure application can reach database

# Test connection from application server
mysql -h ${NEW_DB_ENDPOINT} -u admin -p

# Verify secrets are updated
# Check environment variables or secret manager

# Restart application
```

## Contact Information

- **On-Call Engineer**: [Phone/Pager]
- **Database Admin**: [Phone/Email]
- **Cloud Architect**: [Phone/Email]
- **Escalation**: [Manager Phone/Email]

## Related Runbooks

- [FAILBACK.md](FAILBACK.md) - Returning to original primary
- [DATABASE_PROMOTION.md](DATABASE_PROMOTION.md) - Detailed database promotion steps
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2024-01-15 | 1.0 | DevOps Team | Initial version |
