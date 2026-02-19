# Route 53 DNS and Health Checks Module

This Terraform module configures AWS Route 53 for global DNS routing with health-based failover across AWS, Azure, and GCP.

## Features

- Route 53 hosted zone for domain management
- Health checks for all three clouds (AWS, Azure, GCP)
- Failover routing policy (AWS → Azure → GCP)
- CloudWatch alarms for health check failures
- DNS query logging
- EventBridge integration for health state changes
- CloudWatch dashboard for DNS health monitoring

## Architecture

```
                    ┌─────────────────┐
                    │   Route 53      │
                    │  Hosted Zone    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
         │  AWS    │    │ Azure   │   │  GCP    │
         │ Health  │    │ Health  │   │ Health  │
         │  Check  │    │  Check  │   │  Check  │
         └────┬────┘    └────┬────┘   └────┬────┘
              │              │              │
         ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
         │   AWS   │    │  Azure  │   │   GCP   │
         │   ALB   │    │   LB    │   │   LB    │
         └─────────┘    └─────────┘   └─────────┘
```

## Usage

### Basic Configuration

```hcl
module "route53" {
  source = "./terraform/route53"

  project_name = "singha-loyalty"
  environment  = "prod"
  aws_region   = "us-east-1"

  # Domain configuration
  domain_name = "singha-loyalty.example.com"
  dns_ttl     = 60  # Low TTL for rapid failover

  # Health check configuration
  health_check_path     = "/health"
  health_check_interval = 30
  failure_threshold     = 3

  # AWS Primary
  aws_endpoint    = "singha-loyalty-prod-alb-123456789.us-east-1.elb.amazonaws.com"
  aws_ip_address  = "52.1.2.3"

  # Azure Failover
  azure_endpoint    = "singha-loyalty-prod-lb.eastus.cloudapp.azure.com"
  azure_ip_address  = "20.1.2.3"

  # GCP Failover
  gcp_endpoint    = "singha-loyalty-prod-lb.example.com"
  gcp_ip_address  = "35.1.2.3"

  # SNS topic for alerts
  sns_topic_arn = module.sns.topic_arn

  # Logging
  log_retention_days = 90
}
```

### Outputs

```hcl
output "zone_id" {
  value = module.route53.zone_id
}

output "name_servers" {
  value = module.route53.zone_name_servers
}

output "health_check_ids" {
  value = module.route53.health_check_ids
}
```

## Health Checks

### Configuration

Each health check monitors:
- **Protocol**: HTTPS
- **Port**: 443
- **Path**: `/health` (configurable)
- **Interval**: 30 seconds (configurable: 10 or 30)
- **Failure Threshold**: 3 consecutive failures

### Health Check Endpoints

All application endpoints must implement a `/health` endpoint that returns:
- **Status Code**: 200 OK when healthy
- **Response Body**: JSON with health status

Example response:
```json
{
  "status": "healthy",
  "timestamp": "2024-02-15T10:30:00Z",
  "checks": {
    "database": "ok",
    "cache": "ok"
  }
}
```

## Failover Routing

### Priority Order

1. **Primary**: AWS (us-east-1)
2. **Secondary**: Azure (East US)
3. **Tertiary**: GCP (us-central1)

### Failover Logic

Route 53 automatically routes traffic based on health:
- If AWS is healthy → Route to AWS
- If AWS is unhealthy AND Azure is healthy → Route to Azure
- If AWS and Azure are unhealthy AND GCP is healthy → Route to GCP
- If all are unhealthy → Route to last known healthy (with alarm)

### DNS TTL

- **TTL**: 60 seconds
- **Purpose**: Rapid failover propagation
- **Trade-off**: Higher query volume vs. faster failover

## Monitoring

### CloudWatch Alarms

Four alarms are configured:

1. **AWS Health Alarm**
   - Triggers when AWS endpoint is unhealthy
   - Sends SNS notification

2. **Azure Health Alarm**
   - Triggers when Azure endpoint is unhealthy
   - Sends SNS notification

3. **GCP Health Alarm**
   - Triggers when GCP endpoint is unhealthy
   - Sends SNS notification

4. **Overall Health Alarm**
   - CRITICAL: Triggers when ALL endpoints are unhealthy
   - Sends SNS notification

### CloudWatch Dashboard

Access the dashboard:
```bash
aws cloudwatch get-dashboard \
  --dashboard-name singha-loyalty-prod-dns-health
```

Dashboard includes:
- Health check status for all clouds
- Overall health percentage
- Recent DNS queries
- Failover events

### Query Logging

DNS queries are logged to CloudWatch Logs:
```bash
aws logs tail /aws/route53/singha-loyalty-prod --follow
```

Log retention: 90 days (configurable)

## EventBridge Integration

Health check state changes trigger EventBridge events:
- Event source: `aws.route53`
- Event type: `Route 53 Health Check Status Change`
- Target: SNS topic for notifications

## DNS Failover Orchestration

The `dns_failover.py` script provides automated failover orchestration:

```bash
# Set environment variables
export HOSTED_ZONE_ID="Z1234567890ABC"
export DOMAIN_NAME="singha-loyalty.example.com"
export AWS_HEALTH_CHECK_ID="abc123"
export AZURE_HEALTH_CHECK_ID="def456"
export GCP_HEALTH_CHECK_ID="ghi789"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:alerts"

# Run orchestrator
python infrastructure/scripts/dns_failover.py
```

The orchestrator:
- Monitors health checks every 30 seconds
- Detects failures (3 consecutive failures)
- Updates DNS records automatically
- Sends SNS notifications
- Logs events to CloudWatch

## Testing

### Property-Based Tests

Run property tests:
```bash
pytest infrastructure/tests/property/test_dns_routing.py -v
```

Tests verify:
- **Property 3**: DNS routes to healthy primary
- **Property 4**: Failover cascade follows priority
- **Property 6**: DNS updates complete within 60 seconds

### Manual Testing

Test health checks:
```bash
# Check AWS health
aws route53 get-health-check-status \
  --health-check-id $AWS_HEALTH_CHECK_ID

# Check Azure health
aws route53 get-health-check-status \
  --health-check-id $AZURE_HEALTH_CHECK_ID

# Check GCP health
aws route53 get-health-check-status \
  --health-check-id $GCP_HEALTH_CHECK_ID
```

Test DNS resolution:
```bash
# Query DNS
dig singha-loyalty.example.com

# Query with specific nameserver
dig @ns-123.awsdns-12.com singha-loyalty.example.com
```

Simulate failover:
```bash
# Update DNS to Azure
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://failover-to-azure.json
```

## Deployment

### Prerequisites

1. Domain name registered
2. AWS account with Route 53 permissions
3. Load balancers deployed in all clouds
4. SNS topic created for alerts

### Deployment Steps

1. **Initialize Terraform**
   ```bash
   cd infrastructure/terraform/route53
   terraform init
   ```

2. **Configure Variables**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Plan Deployment**
   ```bash
   terraform plan -out=tfplan
   ```

4. **Apply Configuration**
   ```bash
   terraform apply tfplan
   ```

5. **Update Domain Nameservers**
   ```bash
   # Get nameservers
   terraform output zone_name_servers
   
   # Update at domain registrar
   # Point domain to Route 53 nameservers
   ```

6. **Verify Health Checks**
   ```bash
   # Wait 2-3 minutes for health checks to initialize
   aws route53 get-health-check-status \
     --health-check-id $(terraform output -raw health_check_ids.aws)
   ```

## Troubleshooting

### Health Checks Failing

**Issue**: Health checks show unhealthy status

**Solutions**:
1. Verify endpoint is accessible: `curl https://your-endpoint/health`
2. Check security groups allow Route 53 health checkers
3. Verify SSL certificate is valid
4. Check application logs for errors
5. Ensure `/health` endpoint returns 200 OK

### DNS Not Resolving

**Issue**: Domain doesn't resolve

**Solutions**:
1. Verify nameservers are updated at registrar
2. Check hosted zone exists: `aws route53 list-hosted-zones`
3. Verify DNS records: `aws route53 list-resource-record-sets --hosted-zone-id $ZONE_ID`
4. Wait for DNS propagation (up to 48 hours)
5. Test with Route 53 nameservers directly

### Failover Not Working

**Issue**: Traffic doesn't fail over to secondary

**Solutions**:
1. Verify health checks are configured correctly
2. Check failure threshold is reached (3 consecutive failures)
3. Verify secondary endpoint is healthy
4. Check DNS TTL has expired (60 seconds)
5. Review CloudWatch alarms for health check status

### High DNS Query Costs

**Issue**: Route 53 costs are high

**Solutions**:
1. Increase DNS TTL (trade-off: slower failover)
2. Use CloudFront for caching
3. Review query patterns in logs
4. Consider using alias records where possible

## Cost Estimation

### Monthly Costs

- **Hosted Zone**: $0.50/month
- **Health Checks**: $1.50/month (3 checks × $0.50)
- **DNS Queries**: ~$0.40/million queries
- **CloudWatch Logs**: ~$0.50/GB ingested
- **CloudWatch Alarms**: $0.10/alarm × 4 = $0.40

**Total**: ~$3-5/month (excluding query volume)

### Cost Optimization

1. Use calculated health checks to reduce costs
2. Increase health check interval to 30 seconds
3. Reduce log retention period
4. Use CloudWatch Logs Insights for analysis

## Security Best Practices

1. **Enable DNSSEC** for domain validation
2. **Use HTTPS** for all health checks
3. **Restrict health check endpoints** to Route 53 IP ranges
4. **Enable query logging** for audit trail
5. **Use IAM roles** with least privilege
6. **Enable MFA** for Route 53 changes
7. **Monitor for unauthorized changes** via CloudTrail

## Next Steps

After deploying Route 53:

1. **Test failover manually**
   - Simulate AWS failure
   - Verify traffic routes to Azure
   - Measure failover time

2. **Set up monitoring**
   - Configure SNS subscriptions
   - Set up PagerDuty/Slack integration
   - Create runbooks for failover scenarios

3. **Deploy health monitor** (Task 8)
   - Implement continuous health monitoring
   - Set up alerting system
   - Configure centralized logging

4. **Implement failover orchestration** (Task 9)
   - Deploy DNS failover script
   - Configure database promotion
   - Test end-to-end failover

## References

- [Route 53 Documentation](https://docs.aws.amazon.com/route53/)
- [Health Checks](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover.html)
- [Failover Routing](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html#routing-policy-failover)
- [DNS Best Practices](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html)
