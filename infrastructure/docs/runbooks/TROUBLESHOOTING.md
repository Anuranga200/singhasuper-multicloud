# Multi-Cloud DR System - Troubleshooting Guide

## Table of Contents
1. [Health Check Issues](#health-check-issues)
2. [Database Replication Issues](#database-replication-issues)
3. [DNS and Routing Issues](#dns-and-routing-issues)
4. [Application Issues](#application-issues)
5. [Network Connectivity Issues](#network-connectivity-issues)
6. [Performance Issues](#performance-issues)
7. [Cost Issues](#cost-issues)
8. [Monitoring and Alerting Issues](#monitoring-and-alerting-issues)

---

## Health Check Issues

### Issue: Route 53 Health Checks Failing

**Symptoms**:
- Route 53 dashboard shows unhealthy status
- Automated failover triggered unexpectedly
- Health check endpoint returns errors

**Diagnosis**:
```bash
# Check health check status
aws route53 get-health-check-status --health-check-id <health-check-id>

# Test endpoint directly
curl -v https://<endpoint>/health

# Check load balancer target health
aws elbv2 describe-target-health --target-group-arn <arn>
```

**Common Causes**:
1. Application not responding on health endpoint
2. Security group blocking Route 53 IP ranges
3. SSL certificate issues
4. Load balancer misconfiguration

**Solutions**:

**Solution 1: Fix Application Health Endpoint**
```bash
# Check application logs
aws logs tail /aws/ec2/multicloud-dr --follow

# Verify health endpoint code
# Ensure /health returns 200 OK

# Restart application
aws autoscaling start-instance-refresh --auto-scaling-group-name multicloud-dr-asg
```

**Solution 2: Update Security Groups**
```bash
# Allow Route 53 health checker IP ranges
# Add these CIDR blocks to security group:
# 15.177.0.0/18 (us-east-1)
# 54.183.255.128/26 (us-west-1)
# 54.228.16.0/26 (eu-west-1)
# 54.232.40.64/26 (sa-east-1)
# 54.241.32.64/26 (us-west-2)
# 54.243.31.192/26 (us-east-1)
# 107.23.255.0/26 (us-east-1)
# 176.34.159.192/26 (eu-west-1)
# 177.71.207.128/26 (sa-east-1)

aws ec2 authorize-security-group-ingress \
  --group-id <sg-id> \
  --protocol tcp \
  --port 443 \
  --cidr 15.177.0.0/18
```

**Solution 3: Verify SSL Certificate**
```bash
# Check certificate expiration
echo | openssl s_client -servername your-domain.com -connect <endpoint>:443 2>/dev/null | openssl x509 -noout -dates

# Renew certificate if expired
# For AWS ACM:
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS
```

---

## Database Replication Issues

### Issue: Replication Lag High

**Symptoms**:
- `Seconds_Behind_Master` > 60
- Data not appearing in replicas
- Failover delayed due to lag

**Diagnosis**:
```sql
-- Check replication status
SHOW SLAVE STATUS\G

-- Check for long-running queries
SELECT * FROM information_schema.processlist WHERE time > 60;

-- Check replica load
SHOW GLOBAL STATUS LIKE 'Threads_running';
```

**Common Causes**:
1. Large transactions on primary
2. Replica under-provisioned
3. Network latency
4. Replica applying changes slowly

**Solutions**:

**Solution 1: Enable Parallel Replication**
```sql
-- For MySQL 5.7+
STOP SLAVE SQL_THREAD;
SET GLOBAL slave_parallel_workers = 4;
SET GLOBAL slave_parallel_type = 'LOGICAL_CLOCK';
START SLAVE SQL_THREAD;

-- Verify
SHOW VARIABLES LIKE 'slave_parallel%';
```

**Solution 2: Optimize Replica Performance**
```bash
# Scale up replica instance
# AWS RDS
aws rds modify-db-instance \
  --db-instance-identifier multicloud-dr-rds \
  --db-instance-class db.t3.small \
  --apply-immediately

# Azure
az mysql server update \
  --resource-group multicloud-dr-rg \
  --name multicloud-dr-mysql \
  --sku-name GP_Gen5_2

# GCP
gcloud sql instances patch multicloud-dr-cloudsql \
  --tier=db-n1-standard-1
```

**Solution 3: Reduce Primary Load**
```sql
-- Identify slow queries on primary
SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;

-- Optimize queries
-- Add indexes where needed
-- Break large transactions into smaller ones
```

### Issue: Replication Stopped

**Symptoms**:
- `Slave_IO_Running: No` or `Slave_SQL_Running: No`
- Error in `Last_Error` field
- Data not replicating

**Diagnosis**:
```sql
SHOW SLAVE STATUS\G

-- Check specific error
-- Last_IO_Error: <error message>
-- Last_SQL_Error: <error message>
```

**Common Errors and Solutions**:

**Error 1062: Duplicate Entry**
```sql
-- Skip the duplicate entry
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;

-- Or if persistent, resync replica
-- See "Resync Replica" procedure below
```

**Error 1032: Can't Find Record**
```sql
-- Skip the missing record
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;

-- Or resync if data integrity critical
```

**Error 2003: Can't Connect to MySQL Server**
```bash
# Check network connectivity
telnet <primary-host> 3306

# Check firewall rules
# Verify replication user credentials
mysql -h <primary-host> -u replication_user -p

# Check primary is accessible
aws rds describe-db-instances --db-instance-identifier <primary-id>
```

**Resync Replica Procedure**:
```bash
# 1. Get primary binary log position
mysql -h <primary> -u admin -p -e "SHOW MASTER STATUS\G"

# 2. Stop replica
mysql -h <replica> -u admin -p -e "STOP SLAVE;"

# 3. Dump data from primary
mysqldump -h <primary> -u admin -p --all-databases --master-data=2 > dump.sql

# 4. Restore to replica
mysql -h <replica> -u admin -p < dump.sql

# 5. Reconfigure replication
mysql -h <replica> -u admin -p
CHANGE MASTER TO
  MASTER_HOST='<primary>',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='password',
  MASTER_LOG_FILE='<from-dump>',
  MASTER_LOG_POS=<from-dump>;
START SLAVE;
```

---

## DNS and Routing Issues

### Issue: DNS Not Resolving to Correct Cloud

**Symptoms**:
- Traffic going to wrong cloud
- Failover not working
- Users seeing old IP address

**Diagnosis**:
```bash
# Check DNS resolution
dig your-domain.com +short

# Check from multiple locations
nslookup your-domain.com 8.8.8.8
nslookup your-domain.com 1.1.1.1

# Check Route 53 records
aws route53 list-resource-record-sets --hosted-zone-id <zone-id>

# Check health check status
aws route53 get-health-check-status --health-check-id <id>
```

**Solutions**:

**Solution 1: Clear DNS Cache**
```bash
# Client-side
# Linux
sudo systemd-resolve --flush-caches

# macOS
sudo dscacheutil -flushcache

# Windows
ipconfig /flushdns

# Server-side (if using DNS forwarder)
# Restart DNS service
```

**Solution 2: Update Route 53 Record**
```bash
# Manually update to correct IP
aws route53 change-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "your-domain.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "<correct-ip>"}]
      }
    }]
  }'

# Verify change
aws route53 get-change --id <change-id>
```

**Solution 3: Fix Health Checks**
```bash
# Update health check configuration
aws route53 update-health-check \
  --health-check-id <id> \
  --resource-path /health \
  --failure-threshold 3

# Test health check endpoint
curl -v https://<endpoint>/health
```

### Issue: Failover Not Triggering

**Symptoms**:
- Primary cloud down but DNS not updating
- Health checks passing but should fail
- Manual failover required

**Diagnosis**:
```bash
# Check health monitor service
ps aux | grep health_monitor

# Check health monitor logs
tail -f /var/log/health_monitor.log

# Check Route 53 health check configuration
aws route53 get-health-check --health-check-id <id>
```

**Solutions**:

**Solution 1: Restart Health Monitor**
```bash
# Stop health monitor
pkill -f health_monitor.py

# Start health monitor
nohup python scripts/health_monitor.py > /var/log/health_monitor.log 2>&1 &

# Verify running
ps aux | grep health_monitor
```

**Solution 2: Adjust Health Check Thresholds**
```bash
# Make health checks more sensitive
aws route53 update-health-check \
  --health-check-id <id> \
  --failure-threshold 2 \
  --request-interval 30
```

**Solution 3: Manual Failover**
```bash
# Trigger manual failover
python scripts/failover_orchestrator.py --manual-failover --target azure

# Or follow MANUAL_FAILOVER.md runbook
```

---

## Application Issues

### Issue: Application Not Starting

**Symptoms**:
- EC2/VM instances running but application not responding
- Health checks failing
- Container errors in logs

**Diagnosis**:
```bash
# Check instance status
# AWS
aws ec2 describe-instances --instance-ids <id>

# Azure
az vm get-instance-view --resource-group multicloud-dr-rg --name <vm-name>

# GCP
gcloud compute instances describe <instance-name>

# Check application logs
# AWS
aws logs tail /aws/ec2/multicloud-dr --follow

# SSH to instance and check
ssh ec2-user@<instance-ip>
docker ps
docker logs <container-id>
```

**Solutions**:

**Solution 1: Restart Application Container**
```bash
# SSH to instance
ssh ec2-user@<instance-ip>

# Restart container
docker restart <container-id>

# Or restart Docker service
sudo systemctl restart docker

# Verify
docker ps
curl localhost:3000/health
```

**Solution 2: Check Environment Variables**
```bash
# Verify secrets are accessible
aws secretsmanager get-secret-value --secret-id /multicloud-dr/db/password

# Check environment variables in container
docker exec <container-id> env

# Update if needed
docker stop <container-id>
docker rm <container-id>
# Restart with correct environment
```

**Solution 3: Rebuild and Redeploy**
```bash
# Pull latest image
docker pull your-registry/your-app:latest

# Stop old container
docker stop <container-id>
docker rm <container-id>

# Start new container
docker run -d -p 3000:3000 \
  -e DB_HOST=<db-endpoint> \
  -e DB_USER=admin \
  -e DB_PASSWORD=<from-secrets> \
  your-registry/your-app:latest
```

### Issue: Database Connection Errors

**Symptoms**:
- Application logs show "Can't connect to MySQL server"
- 500 errors on API endpoints
- Timeout errors

**Diagnosis**:
```bash
# Test database connectivity from application server
mysql -h <db-endpoint> -u admin -p

# Check security groups
aws ec2 describe-security-groups --group-ids <app-sg> <db-sg>

# Check database status
aws rds describe-db-instances --db-instance-identifier <id>

# Check connection count
mysql -h <db-endpoint> -u admin -p -e "SHOW STATUS LIKE 'Threads_connected';"
```

**Solutions**:

**Solution 1: Fix Security Groups**
```bash
# Allow application security group to access database
aws ec2 authorize-security-group-ingress \
  --group-id <db-sg-id> \
  --protocol tcp \
  --port 3306 \
  --source-group <app-sg-id>
```

**Solution 2: Increase Connection Limit**
```sql
-- Check current limit
SHOW VARIABLES LIKE 'max_connections';

-- Increase limit
SET GLOBAL max_connections = 500;

-- For permanent change, update parameter group
```

**Solution 3: Fix Connection Pool**
```javascript
// In application code, adjust connection pool settings
const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  connectionLimit: 10,  // Reduce if too high
  connectTimeout: 10000,
  acquireTimeout: 10000
});
```

---

## Network Connectivity Issues

### Issue: Cross-Cloud Replication Failing

**Symptoms**:
- Replication from AWS to Azure/GCP not working
- Connection timeouts
- Firewall errors

**Diagnosis**:
```bash
# Test connectivity from replica to primary
# From Azure VM
telnet <aws-rds-endpoint> 3306

# From GCP instance
nc -zv <aws-rds-endpoint> 3306

# Check network ACLs and security groups
aws ec2 describe-network-acls
aws ec2 describe-security-groups
```

**Solutions**:

**Solution 1: Allow Cross-Cloud Traffic**
```bash
# AWS: Allow Azure and GCP IP ranges
# Get Azure datacenter IP ranges from Microsoft
# Get GCP IP ranges from Google

# Add to RDS security group
aws ec2 authorize-security-group-ingress \
  --group-id <rds-sg-id> \
  --protocol tcp \
  --port 3306 \
  --cidr <azure-ip-range>

aws ec2 authorize-security-group-ingress \
  --group-id <rds-sg-id> \
  --protocol tcp \
  --port 3306 \
  --cidr <gcp-ip-range>
```

**Solution 2: Use VPN or Private Link**
```bash
# Set up VPN between clouds for secure replication
# AWS Site-to-Site VPN
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id <cgw-id> \
  --vpn-gateway-id <vgw-id>

# Or use cloud-specific private connectivity
# AWS PrivateLink, Azure Private Link, GCP Private Service Connect
```

### Issue: Load Balancer Not Routing Traffic

**Symptoms**:
- 502/503 errors from load balancer
- Requests timing out
- No traffic reaching instances

**Diagnosis**:
```bash
# Check load balancer status
# AWS
aws elbv2 describe-load-balancers --names multicloud-dr-alb
aws elbv2 describe-target-health --target-group-arn <arn>

# Azure
az network lb show --resource-group multicloud-dr-rg --name multicloud-dr-lb
az network lb probe show --resource-group multicloud-dr-rg --lb-name multicloud-dr-lb --name health-probe

# GCP
gcloud compute forwarding-rules describe multicloud-dr-lb --global
gcloud compute backend-services get-health multicloud-dr-backend --global
```

**Solutions**:

**Solution 1: Fix Unhealthy Targets**
```bash
# Check why targets are unhealthy
aws elbv2 describe-target-health --target-group-arn <arn>

# Common issues:
# - Health check path wrong
# - Security group blocking health checks
# - Application not responding

# Fix health check
aws elbv2 modify-target-group \
  --target-group-arn <arn> \
  --health-check-path /health \
  --health-check-interval-seconds 30
```

**Solution 2: Register Targets**
```bash
# Check if instances are registered
aws elbv2 describe-target-health --target-group-arn <arn>

# Register missing instances
aws elbv2 register-targets \
  --target-group-arn <arn> \
  --targets Id=<instance-id>
```

---

## Performance Issues

### Issue: High Response Times

**Symptoms**:
- API requests taking > 1 second
- Database queries slow
- Users reporting slowness

**Diagnosis**:
```bash
# Check application metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=<alb-arn> \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Check database performance
mysql -h <db-endpoint> -u admin -p -e "SHOW PROCESSLIST;"
mysql -h <db-endpoint> -u admin -p -e "SHOW GLOBAL STATUS LIKE 'Slow_queries';"

# Check instance CPU/memory
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=multicloud-dr-asg \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

**Solutions**:

**Solution 1: Scale Up Resources**
```bash
# Increase instance count
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name multicloud-dr-asg \
  --desired-capacity 4

# Or scale up instance size
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name multicloud-dr-asg \
  --launch-template LaunchTemplateName=multicloud-dr-lt,Version='$Latest'
```

**Solution 2: Optimize Database Queries**
```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;

-- Analyze slow queries
SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;

-- Add indexes
EXPLAIN SELECT * FROM customers WHERE email = 'test@example.com';
CREATE INDEX idx_email ON customers(email);
```

**Solution 3: Add Caching**
```javascript
// Add Redis caching layer
const redis = require('redis');
const client = redis.createClient({
  host: process.env.REDIS_HOST,
  port: 6379
});

// Cache frequently accessed data
app.get('/api/customers/:id', async (req, res) => {
  const cacheKey = `customer:${req.params.id}`;
  
  // Check cache first
  const cached = await client.get(cacheKey);
  if (cached) {
    return res.json(JSON.parse(cached));
  }
  
  // Query database
  const customer = await db.query('SELECT * FROM customers WHERE id = ?', [req.params.id]);
  
  // Cache result
  await client.setex(cacheKey, 300, JSON.stringify(customer));
  
  res.json(customer);
});
```

---

## Cost Issues

### Issue: Unexpected High Costs

**Symptoms**:
- Cloud bill higher than expected
- Budget alerts triggered
- Resources running unnecessarily

**Diagnosis**:
```bash
# Check cost breakdown
python cost/cost_monitor.py --detailed

# Check running resources
# AWS
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
aws rds describe-db-instances
aws elbv2 describe-load-balancers

# Azure
az vm list --query "[].{Name:name, State:powerState, Size:hardwareProfile.vmSize}"
az mysql server list

# GCP
gcloud compute instances list
gcloud sql instances list
```

**Solutions**:

**Solution 1: Stop Non-Production Resources**
```bash
# Stop development/test environments
aws ec2 stop-instances --instance-ids <dev-instance-ids>

# Delete unused resources
aws ec2 terminate-instances --instance-ids <unused-instance-ids>
```

**Solution 2: Right-Size Resources**
```bash
# Downgrade over-provisioned instances
aws rds modify-db-instance \
  --db-instance-identifier multicloud-dr-rds \
  --db-instance-class db.t3.micro \
  --apply-immediately

# Reduce auto-scaling max capacity
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name multicloud-dr-asg \
  --max-size 5
```

**Solution 3: Use Reserved Instances**
```bash
# Purchase reserved instances for predictable workloads
aws ec2 purchase-reserved-instances-offering \
  --reserved-instances-offering-id <offering-id> \
  --instance-count 2
```

---

## Monitoring and Alerting Issues

### Issue: Alerts Not Being Sent

**Symptoms**:
- No email/SMS alerts received
- Issues not detected
- Monitoring dashboard not updating

**Diagnosis**:
```bash
# Check SNS topic subscriptions
aws sns list-subscriptions-by-topic --topic-arn <topic-arn>

# Check CloudWatch alarms
aws cloudwatch describe-alarms --state-value ALARM

# Test alert sending
python scripts/failover_orchestrator.py --test-alert
```

**Solutions**:

**Solution 1: Verify SNS Subscriptions**
```bash
# List subscriptions
aws sns list-subscriptions

# Confirm pending subscriptions
# Check email for confirmation link

# Resubscribe if needed
aws sns subscribe \
  --topic-arn <topic-arn> \
  --protocol email \
  --notification-endpoint your-email@example.com
```

**Solution 2: Fix CloudWatch Alarms**
```bash
# Check alarm configuration
aws cloudwatch describe-alarms --alarm-names multicloud-dr-health-alarm

# Update alarm if misconfigured
aws cloudwatch put-metric-alarm \
  --alarm-name multicloud-dr-health-alarm \
  --alarm-description "Alert on health check failures" \
  --metric-name HealthCheckStatus \
  --namespace AWS/Route53 \
  --statistic Minimum \
  --period 60 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions <sns-topic-arn>
```

---

## Emergency Contacts

- **On-Call Engineer**: [Phone/Pager]
- **Database Admin**: [Phone/Email]
- **Network Engineer**: [Phone/Email]
- **Cloud Architect**: [Phone/Email]
- **Escalation Manager**: [Phone/Email]

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) - Deployment procedures
- [MANUAL_FAILOVER.md](MANUAL_FAILOVER.md) - Failover procedures
- [FAILBACK.md](FAILBACK.md) - Failback procedures

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2024-01-15 | 1.0 | DevOps Team | Initial version |
