# 🟡 MEDIUM COST PLAN - Step-by-Step Setup Guide
**Estimated Cost: $60-150/month**

---

## Step 1: Enable CloudTrail (Multi-Region)
**Cost: ~$10-20/month** | **Time: 10 minutes**

### Why Multi-Region CloudTrail?
Captures API activity across all AWS regions for comprehensive security monitoring.

### Setup Instructions:

1. **Navigate to CloudTrail**
   - Go to AWS Console → Search "CloudTrail" → Click "CloudTrail"

2. **Create Trail**
   - Click "Create trail"
   - Trail name: `production-security-trail`
   - ✅ Enable for all regions
   - Storage location: Create new S3 bucket
   - Bucket name: `prod-cloudtrail-logs-[random-number]`
   - ✅ Enable log file validation
   - ✅ Enable CloudWatch Logs (for real-time monitoring)
   - CloudWatch log group: `/aws/cloudtrail/security`

3. **Choose Events**
   - ✅ Management events: All
   - ✅ Data events: S3 buckets (select critical buckets only)
   - ❌ Insights events (optional, adds cost)
   - Read/Write events: Select "All"

4. **Configure Tags**
   - Add tags:
     - Environment: Production
     - Purpose: Security-Monitoring
     - CostCenter: Security

5. **Review and Create**
   - Click "Create trail"

### Cost Optimization:
- Enable data events only for critical S3 buckets
- Use S3 Intelligent-Tiering for log storage
- Set lifecycle policy: Glacier after 30 days, delete after 365 days

---

## Step 2: Enable GuardDuty (Full Features)
**Cost: ~$20-50/month** | **Time: 5 minutes**

### Setup Instructions:

1. **Navigate to GuardDuty**
   - Go to AWS Console → Search "GuardDuty"

2. **Enable GuardDuty**
   - Click "Get Started" → "Enable GuardDuty"

3. **Enable Additional Protections**
   - Go to "Settings" → "Protection plans"
   - ✅ S3 Protection (monitors S3 data events)
   - ✅ EKS Protection (if using Kubernetes)
   - ❌ Malware Protection (expensive, enable if needed)

4. **Configure Findings Export**
   - Go to "Settings" → "Findings export options"
   - Export frequency: "15 minutes"
   - Create S3 bucket: `guardduty-findings-[account-id]`
   - Enable encryption

5. **Set Up Automated Response**
   - Create SNS topic: `guardduty-critical-alerts`
   - Create EventBridge rule for HIGH/CRITICAL findings
   - Subscribe email and/or Slack webhook

### Advanced Configuration:
- Create suppression rules for known false positives
- Set up Lambda function for automated remediation
- Enable trusted IP lists for your office/VPN

---

## Step 3: Enable AWS Config
**Cost: ~$10-30/month** | **Time: 15 minutes**

### Why AWS Config?
Tracks resource configuration changes and compliance with security policies.

### Setup Instructions:

1. **Navigate to AWS Config**
   - Go to AWS Console → Search "Config"

2. **Set Up Config**
   - Click "Get started"
   - ✅ Record all resources in this region
   - ✅ Include global resources (IAM, etc.)
   - S3 bucket: Create new bucket `config-logs-[account-id]`
   - SNS topic: Create new topic `config-notifications`

3. **Choose Managed Rules** (Start with these 10 essential rules)
   - `s3-bucket-public-read-prohibited`
   - `s3-bucket-public-write-prohibited`
   - `encrypted-volumes`
   - `rds-storage-encrypted`
   - `iam-password-policy`
   - `root-account-mfa-enabled`
   - `ec2-security-group-attached-to-eni`
   - `vpc-flow-logs-enabled`
   - `cloudtrail-enabled`
   - `iam-user-mfa-enabled`

4. **Configure Remediation** (Optional)
   - For each rule, you can enable automatic remediation
   - Start with manual remediation to understand impact

### Cost Optimization:
- Limit to 10-15 critical rules initially
- Record only specific resource types if possible
- Use conformance packs for grouped rules


---

## Step 4: Enable Amazon Inspector
**Cost: ~$15-40/month** | **Time: 10 minutes**

### Why Inspector?
Automated vulnerability scanning for EC2 instances and container images.

### Setup Instructions:

1. **Navigate to Inspector**
   - Go to AWS Console → Search "Inspector"

2. **Enable Inspector**
   - Click "Get started"
   - Click "Enable Inspector"

3. **Choose Scan Types**
   - ✅ EC2 scanning (for EC2 instances)
   - ✅ ECR scanning (for container images)
   - ❌ Lambda scanning (enable if using Lambda extensively)

4. **Configure Scanning**
   - Scan frequency: Continuous (recommended)
   - Auto-enable for new resources: ✅ Enabled

5. **Set Up Notifications**
   - Go to "Settings"
   - Create SNS topic: `inspector-findings`
   - Configure alerts for HIGH and CRITICAL vulnerabilities

6. **Review Findings**
   - Go to "Findings"
   - Filter by severity
   - Export findings to S3 for reporting

### Cost Optimization:
- Start with EC2 scanning only
- Enable ECR scanning only for production images
- Review findings weekly and suppress false positives

---

## Step 5: Enable Security Hub (Full Integration)
**Cost: ~$0.001 per security check** | **Time: 10 minutes**

### Setup Instructions:

1. **Navigate to Security Hub**
   - Go to AWS Console → Search "Security Hub"

2. **Enable Security Hub**
   - Click "Go to Security Hub" → "Enable Security Hub"

3. **Enable Security Standards**
   - ✅ AWS Foundational Security Best Practices
   - ✅ CIS AWS Foundations Benchmark v1.4.0
   - ❌ PCI DSS (only if required for compliance)

4. **Enable Integrations**
   - ✅ GuardDuty
   - ✅ Inspector
   - ✅ IAM Access Analyzer
   - ✅ AWS Config
   - ✅ Firewall Manager (if using)
   - ✅ Macie (if using)

5. **Configure Aggregation** (Multi-Region)
   - Go to "Settings" → "Regions"
   - Select aggregation region (your primary region)
   - Link all regions you use

6. **Set Up Custom Actions**
   - Create EventBridge rules for automated workflows
   - Example: Auto-create Jira tickets for CRITICAL findings

### Advanced Configuration:
- Create custom insights for your specific use cases
- Set up automated remediation with Lambda
- Configure SIEM integration (Splunk, Datadog, etc.)

---

## Step 6: Enable VPC Flow Logs
**Cost: ~$5-15/month** | **Time: 5 minutes per VPC**

### Setup Instructions:

1. **Navigate to VPC**
   - Go to AWS Console → Search "VPC"

2. **Enable Flow Logs**
   - Select your VPC
   - Click "Actions" → "Create flow log"
   - Filter: "All" (Accept and Reject)
   - Destination: CloudWatch Logs
   - Log group: `/aws/vpc/flowlogs`
   - IAM role: Create new role

3. **Configure Log Format** (Optional)
   - Use custom format to reduce costs
   - Include only essential fields:
     - srcaddr, dstaddr, srcport, dstport
     - protocol, action, bytes

4. **Set Retention**
   - Go to CloudWatch → Log groups
   - Select flow log group
   - Set retention: 30 days

### Cost Optimization:
- Use custom log format with fewer fields
- Set short retention period (30 days)
- Consider sampling (50% of traffic) for non-critical VPCs

---

## Step 7: Enable AWS Systems Manager (Session Manager)
**Cost: FREE** | **Time: 10 minutes**

### Why Session Manager?
Secure shell access to EC2 instances without SSH keys or bastion hosts.

### Setup Instructions:

1. **Install SSM Agent** (if not already installed)
   - Most Amazon Linux 2 AMIs have it pre-installed
   - For other OS, follow AWS documentation

2. **Create IAM Role for EC2**
   - Go to IAM → Roles → Create role
   - Use case: EC2
   - Attach policy: `AmazonSSMManagedInstanceCore`
   - Role name: `EC2-SSM-Role`

3. **Attach Role to EC2 Instances**
   - Go to EC2 → Select instance
   - Actions → Security → Modify IAM role
   - Select `EC2-SSM-Role`

4. **Enable Session Logging**
   - Go to Systems Manager → Session Manager → Preferences
   - ✅ Enable CloudWatch logging
   - ✅ Enable S3 logging
   - S3 bucket: `session-logs-[account-id]`

5. **Test Connection**
   - Go to Systems Manager → Fleet Manager
   - Select instance → "Start session"

---

## Step 8: Configure AWS Organizations & Control Tower (Optional)
**Cost: FREE (Control Tower setup)** | **Time: 30 minutes**

### Why Control Tower?
Provides guardrails and governance for multi-account AWS environments.

### Setup Instructions:

1. **Enable AWS Organizations**
   - Go to AWS Organizations
   - Click "Create organization"

2. **Set Up Control Tower**
   - Go to AWS Control Tower
   - Click "Set up landing zone"
   - Select home region
   - Configure organizational units:
     - Security OU
     - Production OU
     - Development OU

3. **Enable Guardrails**
   - Mandatory guardrails (automatically enabled)
   - Strongly recommended guardrails:
     - Detect public S3 buckets
     - Detect unencrypted EBS volumes
     - Detect root account usage

4. **Configure Account Factory**
   - Set up automated account provisioning
   - Define baseline security configurations

### Note:
Control Tower is free, but creates additional AWS accounts which may incur costs for services used in those accounts.

---

## Step 9: Set Up Comprehensive CloudWatch Alarms
**Cost: ~$1-5/month** | **Time: 20 minutes**

### Critical Alarms to Create:

1. **Root Account Usage**
   - Metric filter: Root account login
   - Threshold: > 0
   - Action: SNS notification

2. **Unauthorized API Calls**
   - Metric filter: UnauthorizedOperation or AccessDenied
   - Threshold: > 5 in 5 minutes
   - Action: SNS notification

3. **IAM Policy Changes**
   - Metric filter: IAM policy modifications
   - Threshold: > 0
   - Action: SNS notification

4. **Security Group Changes**
   - Metric filter: Security group modifications
   - Threshold: > 0
   - Action: SNS notification

5. **Network ACL Changes**
   - Metric filter: NACL modifications
   - Threshold: > 0
   - Action: SNS notification

6. **Console Login Failures**
   - Metric filter: Failed console logins
   - Threshold: > 3 in 5 minutes
   - Action: SNS notification

### Setup Process:
1. Go to CloudWatch → Logs → Log groups
2. Select CloudTrail log group
3. Create metric filters for each alarm
4. Create alarms based on metrics
5. Configure SNS notifications

---

## Step 10: Enable AWS Backup (Security Perspective)
**Cost: Storage costs only** | **Time: 15 minutes**

### Setup Instructions:

1. **Navigate to AWS Backup**
   - Go to AWS Console → Search "Backup"

2. **Create Backup Plan**
   - Click "Create backup plan"
   - Plan name: `security-backup-plan`
   - Backup rule:
     - Frequency: Daily
     - Retention: 30 days
     - Copy to another region: ✅ (for disaster recovery)

3. **Assign Resources**
   - Select resource types:
     - RDS databases
     - EBS volumes
     - EFS file systems
   - Use tags to auto-assign: `Backup: true`

4. **Enable Backup Vault Lock**
   - Prevents deletion of backups (ransomware protection)
   - Set minimum retention: 30 days

---

## Verification and Testing

### Week 1 - Initial Verification:

1. **CloudTrail**
   - [ ] Logs appearing in S3
   - [ ] CloudWatch Logs receiving events
   - [ ] Multi-region coverage confirmed

2. **GuardDuty**
   - [ ] Generate sample findings
   - [ ] Verify SNS notifications
   - [ ] Check S3 protection status

3. **AWS Config**
   - [ ] Configuration items being recorded
   - [ ] Compliance rules evaluating
   - [ ] Non-compliant resources identified

4. **Inspector**
   - [ ] EC2 instances being scanned
   - [ ] Findings appearing
   - [ ] Vulnerability reports generated

5. **Security Hub**
   - [ ] All integrations active
   - [ ] Security score visible
   - [ ] Findings from all sources

---

## Monthly Maintenance Schedule

### Week 1:
- [ ] Review GuardDuty findings (HIGH/CRITICAL)
- [ ] Check Inspector vulnerability reports
- [ ] Review Security Hub compliance score
- [ ] Analyze CloudTrail unusual activity

### Week 2:
- [ ] Review AWS Config compliance status
- [ ] Remediate non-compliant resources
- [ ] Check IAM Access Analyzer findings
- [ ] Review VPC Flow Logs for anomalies

### Week 3:
- [ ] Security Hub findings review
- [ ] Update suppression rules
- [ ] Review CloudWatch alarm history
- [ ] Check billing for security services

### Week 4:
- [ ] Monthly security report generation
- [ ] Review and update security policies
- [ ] Test incident response procedures
- [ ] Archive resolved findings

---

## Cost Monitoring Dashboard

### Create Custom Dashboard:

1. **Go to CloudWatch → Dashboards**
2. **Create dashboard**: `Security-Services-Costs`
3. **Add widgets**:
   - CloudTrail costs (line graph)
   - GuardDuty costs (line graph)
   - Config costs (line graph)
   - Inspector costs (line graph)
   - Total security costs (number widget)

### Set Up Cost Alerts:

1. **Billing Budget**
   - Amount: $150/month
   - Alert at: 80%, 100%, 120%

2. **Service-Specific Budgets**
   - GuardDuty: $50/month
   - Config: $30/month
   - Inspector: $40/month

---

## Incident Response Playbook

### High-Severity GuardDuty Finding:

1. **Immediate Actions** (0-15 minutes)
   - Review finding details
   - Identify affected resources
   - Isolate compromised resources if needed

2. **Investigation** (15-60 minutes)
   - Check CloudTrail for related API calls
   - Review VPC Flow Logs
   - Check Security Hub for related findings

3. **Remediation** (1-4 hours)
   - Apply security patches
   - Rotate credentials
   - Update security groups
   - Document incident

4. **Post-Incident** (1-2 days)
   - Root cause analysis
   - Update security policies
   - Implement preventive measures
   - Team debrief

---

## Troubleshooting Guide

### Issue: High AWS Config Costs
**Solution:**
- Review number of configuration items
- Reduce number of rules
- Limit resource types being recorded
- Check for unnecessary rule evaluations

### Issue: Inspector Not Scanning Instances
**Solution:**
- Verify SSM agent is installed and running
- Check IAM role has required permissions
- Ensure instances are in supported regions
- Review Inspector service status

### Issue: Security Hub Findings Overload
**Solution:**
- Suppress low-severity findings
- Disable unnecessary security standards
- Create custom insights for priority findings
- Set up automated workflows for common issues

### Issue: GuardDuty False Positives
**Solution:**
- Create suppression rules
- Add trusted IP lists
- Review threat lists
- Adjust finding severity thresholds

---

## Next Steps & Advanced Features

### After 2-3 Months:

1. **Consider Adding:**
   - AWS Macie (for S3 data classification)
   - AWS WAF (for web application protection)
   - AWS Shield Advanced (for DDoS protection)
   - AWS Firewall Manager (centralized firewall management)

2. **Automation Opportunities:**
   - Auto-remediation with Lambda
   - SOAR integration (Security Orchestration)
   - Custom security dashboards
   - Automated compliance reporting

3. **Advanced Monitoring:**
   - CloudWatch Insights queries
   - Athena queries on CloudTrail logs
   - Custom threat detection rules
   - Machine learning anomaly detection

---

## Additional Resources

- [AWS Security Hub User Guide](https://docs.aws.amazon.com/securityhub/)
- [GuardDuty Best Practices](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_best-practices.html)
- [AWS Config Best Practices](https://docs.aws.amazon.com/config/latest/developerguide/best-practices.html)
- [Inspector User Guide](https://docs.aws.amazon.com/inspector/)
- [AWS Security Blog](https://aws.amazon.com/blogs/security/)
