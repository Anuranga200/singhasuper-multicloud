# Failback Runbook

## Purpose
This runbook provides step-by-step instructions for failing back to the original primary cloud after a failover event.

## When to Use
- Original primary cloud has been restored and verified stable
- DR drill completion (returning to normal operations)
- Cost optimization (returning to lower-cost primary)
- Performance optimization (returning to better-performing primary)

## Prerequisites
- Successful failover to secondary cloud completed
- Original primary cloud fully operational and tested
- Database replication configured from current primary to original primary
- All stakeholders notified of planned failback
- Maintenance window scheduled (if required)

## Important Considerations

⚠️ **Failback is NOT the reverse of failover**
- Failback requires re-establishing replication in the opposite direction
- Data written to the failover cloud must be replicated back
- Failback typically requires more time than failover (15-30 minutes)
- Failback should be performed during low-traffic periods when possible

---

## Failback Procedure

### Phase 1: Pre-Failback Preparation (10 minutes)

#### Step 1.1: Verify Original Primary Health

**For AWS (typical primary)**:
```bash
# Check EC2 instances
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=multicloud-dr-*" \
  --query "Reservations[].Instances[].[InstanceId,State.Name,PrivateIpAddress]"

# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier multicloud-dr-rds \
  --query "DBInstances[0].[DBInstanceStatus,Endpoint.Address]"

# Check ALB health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Test application endpoint
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names multicloud-dr-alb \
  --query "LoadBalancers[0].DNSName" --output text)

curl -f https://${ALB_DNS}/health || echo "Health check failed"
```

**Expected**: All resources healthy and operational

#### Step 1.2: Establish Reverse Replication

**Current State**: Azure/GCP is primary, AWS is idle

**Goal**: Configure AWS RDS as replica of Azure/GCP database

**From Azure to AWS**:
```bash
# Get current Azure MySQL endpoint
AZURE_MYSQL_SERVER=$(az mysql server show \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-mysql \
  --query "fullyQualifiedDomainName" -o tsv)

# Enable binary logging on Azure (if not already enabled)
az mysql server configuration set \
  --resource-group multicloud-dr-rg \
  --server-name multicloud-dr-mysql \
  --name log_bin \
  --value ON

# Get binary log position
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p -e "SHOW MASTER STATUS\G"
```

**Note**: File name and Position

**Configure AWS RDS as replica**:
```bash
# Get AWS RDS endpoint
AWS_RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier multicloud-dr-rds \
  --query "DBInstances[0].Endpoint.Address" --output text)

# Connect to AWS RDS
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p

# Configure replication from Azure
CHANGE MASTER TO
  MASTER_HOST='<AZURE_MYSQL_SERVER>',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='replication-password',
  MASTER_LOG_FILE='<BINLOG_FILE>',
  MASTER_LOG_POS=<BINLOG_POSITION>;

# Start replication
START SLAVE;

# Verify replication
SHOW SLAVE STATUS\G
```

**Expected**:
- Slave_IO_Running: Yes
- Slave_SQL_Running: Yes

**From GCP to AWS**:
```bash
# Get Cloud SQL instance connection
GCP_SQL_IP=$(gcloud sql instances describe multicloud-dr-cloudsql \
  --format="value(ipAddresses[0].ipAddress)")

# Get binary log position
gcloud sql connect multicloud-dr-cloudsql --user=root
SHOW MASTER STATUS\G
```

**Configure AWS RDS as replica**:
```bash
# Connect to AWS RDS
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p

# Configure replication from GCP
CHANGE MASTER TO
  MASTER_HOST='<GCP_SQL_IP>',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='replication-password',
  MASTER_LOG_FILE='<BINLOG_FILE>',
  MASTER_LOG_POS=<BINLOG_POSITION>;

# Start replication
START SLAVE;

# Verify replication
SHOW SLAVE STATUS\G
```

#### Step 1.3: Wait for Replication to Catch Up

```bash
# Monitor replication lag
watch -n 5 'mysql -h ${AWS_RDS_ENDPOINT} -u admin -p<password> -e "SHOW SLAVE STATUS\G" | grep Seconds_Behind_Master'

# Wait until Seconds_Behind_Master = 0
```

**Typical wait time**: 5-15 minutes depending on data volume

#### Step 1.4: Notify Stakeholders

```bash
# Send notification
python scripts/failover_orchestrator.py --notify \
  --message "Failback to AWS scheduled for [TIME]. Expected downtime: 5-10 minutes" \
  --severity medium
```

**Notify**:
- Operations team
- Development team
- Management
- Customers (if downtime expected)

---

### Phase 2: Application Quiesce (2 minutes)

#### Step 2.1: Enable Maintenance Mode (Optional)

```bash
# If application supports maintenance mode
# Update load balancer to show maintenance page

# For Azure
az network lb rule update \
  --resource-group multicloud-dr-rg \
  --lb-name multicloud-dr-lb \
  --name http-rule \
  --backend-pool-name maintenance-pool

# For GCP
gcloud compute backend-services update multicloud-dr-backend \
  --global \
  --custom-response-header "X-Maintenance-Mode: true"
```

#### Step 2.2: Reduce Traffic (Optional)

```bash
# Gradually reduce traffic to current primary
# This minimizes data that needs to replicate during failback

# Scale down instances (optional)
# Azure
az vmss scale \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-vmss \
  --new-capacity 1

# GCP
gcloud compute instance-groups managed resize \
  multicloud-dr-mig \
  --size 1 \
  --region us-central1
```

---

### Phase 3: Database Failback (3 minutes)

#### Step 3.1: Stop Writes on Current Primary

**For Azure**:
```bash
# Connect to Azure MySQL
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p

# Enable read-only mode
SET GLOBAL read_only = ON;

# Verify no active writes
SHOW PROCESSLIST;

# Wait for any in-flight transactions to complete
SELECT COUNT(*) FROM information_schema.processlist WHERE command != 'Sleep';
```

**For GCP**:
```bash
# Connect to Cloud SQL
gcloud sql connect multicloud-dr-cloudsql --user=root

# Enable read-only mode
SET GLOBAL read_only = ON;

# Verify no active writes
SHOW PROCESSLIST;
```

#### Step 3.2: Verify AWS Replication Caught Up

```bash
# Check replication lag one final time
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p -e "SHOW SLAVE STATUS\G" | grep Seconds_Behind_Master

# Expected: Seconds_Behind_Master: 0
```

**Critical**: Do not proceed if replication lag > 0

#### Step 3.3: Promote AWS RDS to Primary

```bash
# Connect to AWS RDS
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p

# Stop replication
STOP SLAVE;

# Reset slave configuration
RESET SLAVE ALL;

# Disable read-only mode
SET GLOBAL read_only = OFF;

# Verify write capability
USE appdb;
INSERT INTO failover_log (timestamp, event, cloud) VALUES (NOW(), 'Failback to AWS completed', 'AWS');

# Verify insert
SELECT * FROM failover_log ORDER BY timestamp DESC LIMIT 1;
```

**Expected**: Write succeeds

#### Step 3.4: Reconfigure Azure/GCP as Replica

**For Azure**:
```bash
# Get AWS RDS binary log position
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p -e "SHOW MASTER STATUS\G"

# Connect to Azure MySQL
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p

# Configure as replica of AWS
CHANGE MASTER TO
  MASTER_HOST='<AWS_RDS_ENDPOINT>',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='replication-password',
  MASTER_LOG_FILE='<BINLOG_FILE>',
  MASTER_LOG_POS=<BINLOG_POSITION>;

# Start replication
START SLAVE;

# Verify
SHOW SLAVE STATUS\G
```

**For GCP**:
```bash
# Get AWS RDS binary log position
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p -e "SHOW MASTER STATUS\G"

# Connect to Cloud SQL
gcloud sql connect multicloud-dr-cloudsql --user=root

# Configure as replica of AWS
CHANGE MASTER TO
  MASTER_HOST='<AWS_RDS_ENDPOINT>',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='replication-password',
  MASTER_LOG_FILE='<BINLOG_FILE>',
  MASTER_LOG_POS=<BINLOG_POSITION>;

# Start replication
START SLAVE;

# Verify
SHOW SLAVE STATUS\G
```

---

### Phase 4: DNS Update (1 minute)

#### Step 4.1: Update Route 53 to AWS

```bash
# Get AWS ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names multicloud-dr-alb \
  --query "LoadBalancers[0].DNSName" --output text)

# Update Route 53 record
aws route53 change-resource-record-sets \
  --hosted-zone-id <HOSTED_ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "your-domain.com",
        "Type": "CNAME",
        "TTL": 60,
        "ResourceRecords": [{"Value": "'${ALB_DNS}'"}]
      }
    }]
  }'
```

#### Step 4.2: Verify DNS Propagation

```bash
# Check DNS resolution
dig your-domain.com +short

# Wait for TTL expiration (60 seconds)
sleep 60

# Verify again
dig your-domain.com +short
```

**Expected**: DNS resolves to AWS ALB

---

### Phase 5: Application Update (2 minutes)

#### Step 5.1: Update Application Configuration

```bash
# Update database endpoint in AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id /multicloud-dr/db/endpoint \
  --secret-string "${AWS_RDS_ENDPOINT}"

# Restart EC2 instances to pick up new config
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name multicloud-dr-asg
```

#### Step 5.2: Scale Up AWS Resources

```bash
# Scale EC2 Auto Scaling Group back to normal capacity
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name multicloud-dr-asg \
  --desired-capacity 2

# Wait for instances to be healthy
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names multicloud-dr-asg \
  --query "AutoScalingGroups[0].Instances[*].[InstanceId,HealthStatus]"
```

---

### Phase 6: Verification (3 minutes)

#### Step 6.1: Test Application Functionality

```bash
# Test health endpoint
curl -f https://your-domain.com/health

# Test read operation
curl -f https://your-domain.com/api/customers

# Test write operation
curl -X POST https://your-domain.com/api/customers \
  -H "Content-Type: application/json" \
  -d '{"email":"failback-test@example.com","name":"Failback Test"}'

# Verify data in AWS RDS
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p -e "
SELECT * FROM appdb.customers WHERE email='failback-test@example.com';
"
```

**Expected**: All operations succeed

#### Step 6.2: Verify Replication to Secondary Clouds

```bash
# Check Azure replication
mysql -h ${AZURE_MYSQL_SERVER} -u admin@multicloud-dr-mysql -p -e "SHOW SLAVE STATUS\G" | grep -E "Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master"

# Check GCP replication
gcloud sql connect multicloud-dr-cloudsql --user=root
SHOW SLAVE STATUS\G
```

**Expected**:
- Slave_IO_Running: Yes
- Slave_SQL_Running: Yes
- Seconds_Behind_Master: < 30

#### Step 6.3: Monitor System Metrics

```bash
# Check AWS CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=<alb-arn> \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average

# Check for errors
aws logs tail /aws/ec2/multicloud-dr --follow --since 5m
```

**Monitor for**: Error rates, response times, database connections

---

### Phase 7: Post-Failback Actions (5 minutes)

#### Step 7.1: Disable Maintenance Mode

```bash
# If maintenance mode was enabled, disable it
# Restore normal load balancer configuration

# For Azure (if still serving traffic)
az network lb rule update \
  --resource-group multicloud-dr-rg \
  --lb-name multicloud-dr-lb \
  --name http-rule \
  --backend-pool-name normal-pool

# For GCP (if still serving traffic)
gcloud compute backend-services update multicloud-dr-backend \
  --global \
  --remove-custom-response-header "X-Maintenance-Mode"
```

#### Step 7.2: Scale Down Secondary Clouds (Optional)

```bash
# Reduce costs by scaling down secondary clouds to minimum

# Azure
az vmss scale \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-vmss \
  --new-capacity 2

# GCP
gcloud compute instance-groups managed resize \
  multicloud-dr-mig \
  --size 2 \
  --region us-central1
```

#### Step 7.3: Update Monitoring

```bash
# Update monitoring to reflect AWS as primary
python scripts/failover_orchestrator.py --update-monitoring \
  --primary-cloud aws

# Verify alerts are configured
python monitoring/unified_dashboard.py --verify-alerts
```

#### Step 7.4: Document Failback

Update incident ticket with:
- Failback completion time
- Total time for failback process
- Any issues encountered
- Data consistency verification results
- Lessons learned

```bash
# Calculate failback duration
echo "Failback started: <START_TIME>"
echo "Failback completed: $(date)"
echo "Duration: <CALCULATED_MINUTES> minutes"

# Verify data consistency
python scripts/verify_consistency.py --full-check
```

#### Step 7.5: Notify Stakeholders

```bash
# Send completion notification
python scripts/failover_orchestrator.py --notify \
  --message "Failback to AWS completed successfully. System operating normally." \
  --severity resolved
```

**Notify**:
- Operations team
- Development team
- Management
- Customers (if notified of maintenance)

---

## Rollback Procedure

If failback fails or causes issues:

### Step 1: Revert DNS to Secondary Cloud

```bash
# Get secondary cloud IP (Azure or GCP)
SECONDARY_IP="<secondary-cloud-ip>"

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
        "ResourceRecords": [{"Value": "'${SECONDARY_IP}'"}]
      }
    }]
  }'
```

### Step 2: Re-promote Secondary Database

```bash
# Stop replication on secondary
STOP SLAVE;
RESET SLAVE ALL;

# Enable writes
SET GLOBAL read_only = OFF;
```

### Step 3: Demote AWS Back to Replica

```bash
# Connect to AWS RDS
mysql -h ${AWS_RDS_ENDPOINT} -u admin -p

# Enable read-only
SET GLOBAL read_only = ON;

# Reconfigure as replica
CHANGE MASTER TO ...
START SLAVE;
```

### Step 4: Notify and Investigate

```bash
# Notify of rollback
python scripts/failover_orchestrator.py --notify \
  --message "Failback rolled back to secondary cloud. Investigating issues." \
  --severity high

# Document rollback reason and investigate root cause
```

---

## Success Criteria

Failback is considered successful when:

- ✅ AWS is primary and accepting writes
- ✅ Azure and GCP are replicas with replication running
- ✅ DNS resolves to AWS
- ✅ Application health checks pass
- ✅ Read and write operations succeed
- ✅ No error spikes in logs
- ✅ Replication lag < 30 seconds
- ✅ Stakeholders notified

## Common Issues

### Issue 1: Replication Won't Start

**Symptom**: Slave_IO_Running: No or Slave_SQL_Running: No

**Solution**:
```bash
# Check network connectivity
telnet <master-host> 3306

# Verify replication user credentials
mysql -h <master-host> -u replication_user -p

# Check binary log file exists
SHOW BINARY LOGS;

# Reset and reconfigure
STOP SLAVE;
RESET SLAVE;
CHANGE MASTER TO ...
START SLAVE;
```

### Issue 2: Data Inconsistency Detected

**Symptom**: Data differs between primary and replicas

**Solution**:
```bash
# Stop failback immediately
# Investigate data discrepancy

# Run consistency check
python scripts/verify_consistency.py --detailed

# If critical, rollback failback
# If minor, document and fix after failback
```

### Issue 3: High Replication Lag

**Symptom**: Seconds_Behind_Master > 60 and not decreasing

**Solution**:
```bash
# Check replica performance
SHOW PROCESSLIST;

# Check for long-running queries
SELECT * FROM information_schema.processlist WHERE time > 60;

# Consider parallel replication (MySQL 5.7+)
SET GLOBAL slave_parallel_workers = 4;
STOP SLAVE SQL_THREAD;
START SLAVE SQL_THREAD;

# Wait for lag to decrease before proceeding
```

### Issue 4: Application Errors After Failback

**Symptom**: 500 errors, database connection failures

**Solution**:
```bash
# Check application logs
aws logs tail /aws/ec2/multicloud-dr --follow

# Verify database endpoint configuration
aws secretsmanager get-secret-value --secret-id /multicloud-dr/db/endpoint

# Verify security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Restart application instances
aws autoscaling start-instance-refresh --auto-scaling-group-name multicloud-dr-asg
```

## Best Practices

1. **Schedule During Low Traffic**: Perform failback during maintenance windows or low-traffic periods

2. **Test in Staging**: Always test failback procedure in staging environment first

3. **Monitor Closely**: Have team members monitoring all systems during failback

4. **Communicate Clearly**: Keep stakeholders informed throughout the process

5. **Document Everything**: Record all steps, timings, and issues for post-mortem

6. **Verify Thoroughly**: Don't rush verification steps - ensure system is stable

7. **Have Rollback Plan**: Be prepared to rollback if issues arise

## Contact Information

- **On-Call Engineer**: [Phone/Pager]
- **Database Admin**: [Phone/Email]
- **Cloud Architect**: [Phone/Email]
- **Escalation**: [Manager Phone/Email]

## Related Runbooks

- [MANUAL_FAILOVER.md](MANUAL_FAILOVER.md) - Failing over to secondary cloud
- [DATABASE_PROMOTION.md](DATABASE_PROMOTION.md) - Database promotion procedures
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2024-01-15 | 1.0 | DevOps Team | Initial version |
