# Monitoring Dashboards and Observability

This module provides comprehensive monitoring and observability across all cloud providers (AWS, Azure, GCP) for the Multi-Cloud Disaster Recovery System.

## Overview

The monitoring module enables:
- Real-time metrics collection from all clouds
- Unified dashboard aggregating multi-cloud metrics
- Cloud-specific dashboards for detailed monitoring
- Automated alerting on critical metrics
- System health status tracking
- RTO/RPO monitoring

## Components

### 1. AWS CloudWatch Dashboard (`aws_cloudwatch_dashboard.py`)

Creates and manages CloudWatch dashboards for AWS infrastructure.

**Metrics Monitored:**
- EC2 CPU utilization, network traffic, status checks
- RDS CPU, connections, IOPS, replication lag, storage
- ALB request count, response time, HTTP status codes, target health

**Usage:**

```bash
# Create CloudWatch dashboard
python aws_cloudwatch_dashboard.py \
  --config monitoring_config.json \
  --action create \
  --dashboard-name MultiCloudDR-AWS

# Create CloudWatch alarms
python aws_cloudwatch_dashboard.py \
  --config monitoring_config.json \
  --action create-alarms

# Delete dashboard
python aws_cloudwatch_dashboard.py \
  --config monitoring_config.json \
  --action delete \
  --dashboard-name MultiCloudDR-AWS
```

**Alarms Created:**
- EC2 High CPU (>80%)
- RDS High CPU (>80%)
- RDS High Replication Lag (>5s)
- RDS Low Storage (<5GB)
- ALB Unhealthy Targets

**View Dashboard:**
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=MultiCloudDR-AWS
```

### 2. Azure Monitor Dashboard (`azure_monitor_dashboard.py`)

Creates and manages Azure Monitor dashboards for Azure infrastructure.

**Metrics Monitored:**
- VM CPU utilization, network traffic
- Azure Database CPU, connections, replication lag, storage
- Load Balancer availability, throughput

**Usage:**

```bash
# Export dashboard template
python azure_monitor_dashboard.py \
  --config monitoring_config.json \
  --action export \
  --output azure_dashboard.json

# Create metric alerts
python azure_monitor_dashboard.py \
  --config monitoring_config.json \
  --action create-alerts
```

**Alerts Created:**
- VM High CPU (>80%)
- Database High CPU (>80%)
- Database High Replication Lag (>5s)
- Database High Storage (>90%)

**Import Dashboard:**
1. Go to Azure Portal: https://portal.azure.com
2. Navigate to Dashboard
3. Click "Upload" and select `azure_dashboard.json`

### 3. GCP Cloud Monitoring Dashboard (`gcp_monitoring_dashboard.py`)

Creates and manages GCP Cloud Monitoring dashboards for GCP infrastructure.

**Metrics Monitored:**
- Compute Engine CPU utilization, network traffic
- Cloud SQL CPU, connections, replication lag, memory
- Load Balancer request count, latency

**Usage:**

```bash
# Create Cloud Monitoring dashboard
python gcp_monitoring_dashboard.py \
  --config monitoring_config.json \
  --action create \
  --dashboard-name MultiCloudDR-GCP

# List existing dashboards
python gcp_monitoring_dashboard.py \
  --config monitoring_config.json \
  --action list

# Create alert policies
python gcp_monitoring_dashboard.py \
  --config monitoring_config.json \
  --action create-alerts

# Delete dashboard
python gcp_monitoring_dashboard.py \
  --config monitoring_config.json \
  --action delete \
  --dashboard-name MultiCloudDR-GCP
```

**Alert Policies Created:**
- Compute Engine High CPU (>80%)
- Cloud SQL High CPU (>80%)
- Cloud SQL High Replication Lag (>5s)

**View Dashboard:**
```
https://console.cloud.google.com/monitoring/dashboards?project=your-project-id
```

### 4. Unified Multi-Cloud Dashboard (`unified_dashboard.py`)

Aggregates metrics from all clouds into a single unified view.

**Features:**
- Real-time metrics from AWS, Azure, and GCP
- Overall system health status
- Active cloud and failover status
- RTO/RPO metrics
- Aggregate request counts and latency
- HTML dashboard generation

**Usage:**

```bash
# Generate HTML dashboard
python unified_dashboard.py \
  --config monitoring_config.json \
  --action generate-html \
  --output unified_dashboard.html

# Generate JSON report
python unified_dashboard.py \
  --config monitoring_config.json \
  --action generate-json \
  --output metrics_report.json
```

**Dashboard Sections:**
1. System Health Overview
   - Active cloud
   - Failover clouds
   - Overall status (healthy/degraded/critical)
   - RTO/RPO metrics

2. Aggregate Metrics
   - Total requests
   - Average latency
   - Error rate
   - Maximum replication lag

3. Cloud-Specific Metrics
   - Per-cloud CPU, database, and load balancer metrics
   - Cloud status (active/passive/unhealthy)

**Automated Dashboard Updates:**

Set up cron job for automatic dashboard generation:

```bash
# Update dashboard every 5 minutes
*/5 * * * * /usr/bin/python3 /path/to/unified_dashboard.py --config /path/to/config.json --action generate-html --output /var/www/html/dashboard.html
```

## Configuration

Create a configuration file `monitoring_config.json`:

```json
{
  "aws_region": "us-east-1",
  "aws_db_instance_id": "singha-loyalty-db-primary",
  "sns_topic_arn": "arn:aws:sns:us-east-1:123456789012:alerts",
  
  "azure_subscription_id": "your-azure-subscription-id",
  "azure_resource_group": "singha-loyalty-rg",
  "azure_server_name": "singha-loyalty-mysql-azure",
  "azure_location": "eastus",
  "azure_action_group_id": "/subscriptions/.../actionGroups/alerts",
  
  "gcp_project_id": "your-gcp-project-id",
  "gcp_instance_name": "singha-loyalty-mysql-gcp",
  "gcp_credentials_file": "/path/to/service-account-key.json",
  "gcp_notification_channel": "projects/.../notificationChannels/..."
}
```

## Key Metrics

### Application Metrics

| Metric | Description | Threshold | Alert |
|--------|-------------|-----------|-------|
| CPU Utilization | Compute instance CPU usage | >80% | Warning |
| Memory Utilization | Compute instance memory usage | >85% | Warning |
| Network Traffic | Inbound/outbound network bytes | N/A | Info |
| Request Count | Load balancer requests | N/A | Info |
| Response Time | Load balancer latency | >1000ms | Warning |
| Error Rate | HTTP 5xx errors | >5% | Critical |

### Database Metrics

| Metric | Description | Threshold | Alert |
|--------|-------------|-----------|-------|
| Database CPU | Database CPU utilization | >80% | Warning |
| Connections | Active database connections | >80% of max | Warning |
| Replication Lag | Replica lag in seconds | >5s | Critical |
| Storage Space | Free storage space | <5GB | Critical |
| IOPS | Read/write operations per second | N/A | Info |

### System Health Metrics

| Metric | Description | Target | Alert |
|--------|-------------|--------|-------|
| RTO | Recovery Time Objective | <5 min | >5 min |
| RPO | Recovery Point Objective | <5s | >5s |
| Availability | System uptime percentage | >99.9% | <99.9% |
| Failover Time | Time to complete failover | <5 min | >5 min |

## Alerting

### Alert Severity Levels

1. **Critical** - Immediate action required
   - Replication lag >5 seconds
   - All clouds unhealthy
   - Database storage <5GB
   - Error rate >10%

2. **Warning** - Attention needed
   - CPU >80%
   - Memory >85%
   - Storage <20%
   - Response time >1000ms

3. **Info** - Informational only
   - Failover completed
   - Backup completed
   - Configuration changed

### Alert Channels

Configure alert destinations:

**AWS:**
- SNS Topic for email/SMS
- CloudWatch Alarms
- EventBridge for automation

**Azure:**
- Action Groups for email/SMS
- Metric Alerts
- Log Analytics alerts

**GCP:**
- Notification Channels
- Alert Policies
- Cloud Logging alerts

## Dashboard Access

### AWS CloudWatch
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:
```

### Azure Monitor
```
https://portal.azure.com/#blade/Microsoft_Azure_Monitoring/AzureMonitoringBrowseBlade/dashboards
```

### GCP Cloud Monitoring
```
https://console.cloud.google.com/monitoring/dashboards?project=PROJECT_ID
```

### Unified Dashboard
```
http://your-server/unified_dashboard.html
```

## Monitoring Best Practices

1. **Regular Review**
   - Review dashboards daily
   - Check alerts weekly
   - Analyze trends monthly

2. **Threshold Tuning**
   - Adjust thresholds based on actual usage
   - Reduce false positives
   - Ensure critical alerts are actionable

3. **Dashboard Organization**
   - Keep most important metrics visible
   - Use consistent color schemes
   - Group related metrics together

4. **Alert Fatigue Prevention**
   - Set appropriate thresholds
   - Use alert aggregation
   - Implement alert suppression during maintenance

5. **Documentation**
   - Document alert response procedures
   - Maintain runbooks for common issues
   - Keep contact information updated

## Troubleshooting

### Dashboard Not Showing Data

**Symptoms:** Dashboard displays but no metrics visible

**Solutions:**
1. Verify cloud credentials are valid
2. Check IAM permissions for monitoring APIs
3. Verify resources exist and are running
4. Check time range selection
5. Review CloudWatch/Monitor logs for errors

### Alerts Not Firing

**Symptoms:** Expected alerts not received

**Solutions:**
1. Verify alert policies are enabled
2. Check notification channel configuration
3. Verify SNS/Action Group subscriptions
4. Test alert manually
5. Check alert evaluation period

### High Latency in Metrics

**Symptoms:** Metrics delayed or stale

**Solutions:**
1. Check monitoring API rate limits
2. Verify network connectivity
3. Increase collection frequency
4. Check for API throttling
5. Review monitoring service status

### Missing Metrics

**Symptoms:** Some metrics not collected

**Solutions:**
1. Verify metric names are correct
2. Check resource tags and filters
3. Verify monitoring agent is running
4. Check metric namespace
5. Review IAM permissions

## Dependencies

```bash
# Install required packages
pip install boto3 azure-identity azure-mgmt-monitor google-cloud-monitoring google-cloud-monitoring-dashboards
```

## Security Considerations

1. **Credentials**
   - Use IAM roles and service accounts
   - Rotate credentials regularly
   - Store credentials securely

2. **Access Control**
   - Limit dashboard access to authorized users
   - Use least privilege for monitoring APIs
   - Enable MFA for console access

3. **Data Privacy**
   - Avoid logging sensitive data
   - Mask PII in metrics
   - Comply with data retention policies

4. **Audit Logging**
   - Log all dashboard access
   - Track configuration changes
   - Monitor alert modifications

## Related Documentation

- [Health Monitoring](../scripts/README.md#health-monitoring) - Health check implementation
- [Failover Orchestration](../scripts/README.md#failover-orchestration) - Failover procedures
- [Deployment Guide](../DEPLOYMENT_CHECKLIST.md) - Deployment verification
- [Verification Guide](../VERIFICATION_GUIDE.md) - System verification

## Support

For monitoring and dashboard assistance:
- Primary: DevOps Team (devops@example.com)
- Secondary: SRE Team (sre@example.com)
- Emergency: On-call Engineer (oncall@example.com)
