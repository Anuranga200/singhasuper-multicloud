# 🟢 LOW COST PLAN - Step-by-Step Setup Guide
**Estimated Cost: $10-25/month**

---

## Step 1: Enable CloudTrail (Single Trail)
**Cost: ~$2-5/month** | **Time: 5 minutes**

### Why CloudTrail?
Records all API calls in your AWS account for security auditing and compliance.

### Setup Instructions:

1. **Navigate to CloudTrail**
   - Go to AWS Console → Search "CloudTrail" → Click "CloudTrail"

2. **Create Trail**
   - Click "Create trail"
   - Trail name: `my-security-trail`
   - Storage location: Create new S3 bucket
   - Bucket name: `my-company-cloudtrail-logs-[random-number]`
   - ✅ Enable log file validation
   - ❌ Disable CloudWatch Logs (to save cost)

3. **Choose Events**
   - ✅ Management events only
   - ❌ Data events (expensive)
   - ❌ Insights events (expensive)
   - Read/Write events: Select "All"

4. **Review and Create**
   - Click "Create trail"

### Cost Optimization Tips:
- Use S3 Lifecycle policies to delete logs after 90 days
- Keep only management events
- Single region trail (your primary region)

---

## Step 2: Enable GuardDuty (Essential)
**Cost: ~$5-15/month** | **Time: 3 minutes**

### Why GuardDuty?
Intelligent threat detection that monitors for malicious activity and unauthorized behavior.

### Setup Instructions:

1. **Navigate to GuardDuty**
   - Go to AWS Console → Search "GuardDuty" → Click "GuardDuty"

2. **Enable GuardDuty**
   - Click "Get Started"
   - Click "Enable GuardDuty"
   - That's it! GuardDuty is now active

3. **Configure Findings (Optional)**
   - Go to "Settings"
   - Set finding export frequency: "15 minutes" (default)
   - ❌ Don't enable S3 Protection (costs extra)
   - ❌ Don't enable EKS Protection (costs extra)
   - ❌ Don't enable Malware Protection (costs extra)

4. **Set Up Email Notifications**
   - Go to "Settings" → "Findings export options"
   - Create SNS topic for high-severity findings
   - Subscribe your email to the topic

### Cost Optimization Tips:
- Monitor only VPC Flow Logs, DNS logs, and CloudTrail
- Disable S3 and EKS protection initially
- Review findings weekly instead of real-time

---

## Step 3: Enable Security Hub (Basic)
**Cost: ~$0.001 per security check** | **Time: 5 minutes**

### Why Security Hub?
Centralized view of security alerts and compliance status across AWS services.

### Setup Instructions:

1. **Navigate to Security Hub**
   - Go to AWS Console → Search "Security Hub" → Click "Security Hub"

2. **Enable Security Hub**
   - Click "Go to Security Hub"
   - Click "Enable Security Hub"

3. **Choose Security Standards**
   - ✅ AWS Foundational Security Best Practices (Free)
   - ❌ CIS AWS Foundations Benchmark (generates more checks = more cost)
   - ❌ PCI DSS (only if required)

4. **Configure Integrations**
   - ✅ Enable GuardDuty integration (automatic)
   - ✅ Enable IAM Access Analyzer integration

5. **Set Up Notifications**
   - Go to "Settings" → "Custom actions"
   - Create SNS topic for critical findings
   - Subscribe your email

### Cost Optimization Tips:
- Enable only AWS Foundational Security Best Practices
- Suppress non-critical findings
- Review findings weekly

---

## Step 4: Enable IAM Access Analyzer
**Cost: FREE** | **Time: 2 minutes**

### Why IAM Access Analyzer?
Identifies resources shared with external entities and helps you understand access permissions.

### Setup Instructions:

1. **Navigate to IAM**
   - Go to AWS Console → Search "IAM" → Click "IAM"

2. **Enable Access Analyzer**
   - In left menu, click "Access analyzer"
   - Click "Create analyzer"
   - Analyzer name: `my-access-analyzer`
   - Zone of trust: "Current account"
   - Click "Create analyzer"

3. **Review Findings**
   - Access Analyzer will scan your resources
   - Review any findings for publicly accessible resources
   - Archive expected findings

### Cost Optimization Tips:
- It's free! No optimization needed
- Review findings monthly

---

## Step 5: Set Up CloudWatch Alarms (Basic)
**Cost: ~$0.10-1/month** | **Time: 10 minutes**

### Why CloudWatch Alarms?
Get notified of unusual activity or security events.

### Setup Instructions:

1. **Create SNS Topic for Alerts**
   - Go to AWS Console → Search "SNS" → Click "Simple Notification Service"
   - Click "Topics" → "Create topic"
   - Type: Standard
   - Name: `security-alerts`
   - Click "Create topic"
   - Click "Create subscription"
   - Protocol: Email
   - Endpoint: your-email@example.com
   - Click "Create subscription"
   - Check your email and confirm subscription

2. **Create Billing Alarm**
   - Go to CloudWatch → "Alarms" → "Billing"
   - Click "Create alarm"
   - Metric: "Total Estimated Charge"
   - Threshold: $50 (adjust to your budget)
   - SNS topic: `security-alerts`
   - Alarm name: `billing-alert-50`
   - Click "Create alarm"

3. **Create Root Account Usage Alarm**
   - Go to CloudWatch → "Logs" → "Log groups"
   - If you enabled CloudWatch Logs for CloudTrail, create metric filter:
   - Filter pattern: `{ $.userIdentity.type = "Root" && $.userIdentity.invokedBy NOT EXISTS }`
   - Metric name: `RootAccountUsage`
   - Create alarm when metric > 0

### Cost Optimization Tips:
- Limit to 5-10 critical alarms
- Use SNS email instead of SMS (SMS costs more)

---

## Step 6: Enable AWS Trusted Advisor (Basic)
**Cost: FREE (Basic checks)** | **Time: 2 minutes**

### Why Trusted Advisor?
Provides recommendations for cost optimization, security, and performance.

### Setup Instructions:

1. **Navigate to Trusted Advisor**
   - Go to AWS Console → Search "Trusted Advisor"

2. **Review Security Checks**
   - Click "Security" tab
   - Review recommendations:
     - Security Groups - Unrestricted Access
     - IAM Use
     - MFA on Root Account
     - S3 Bucket Permissions

3. **Set Up Weekly Email Notifications**
   - Click "Preferences"
   - ✅ Enable weekly email notifications
   - Add your email
   - Click "Save"

---

## Step 7: Configure S3 Bucket Security
**Cost: FREE** | **Time: 5 minutes**

### Setup Instructions:

1. **Block Public Access (Account Level)**
   - Go to S3 → "Block Public Access settings for this account"
   - ✅ Enable all 4 settings
   - Click "Save changes"

2. **Enable S3 Bucket Versioning** (for CloudTrail bucket)
   - Go to your CloudTrail S3 bucket
   - Click "Properties" → "Bucket Versioning"
   - Click "Enable"

3. **Set Lifecycle Policy** (to reduce storage costs)
   - Go to "Management" → "Lifecycle rules"
   - Create rule: `delete-old-logs`
   - Transition to Glacier after 30 days
   - Delete after 90 days

---

## Step 8: Verify and Test
**Time: 10 minutes**

### Verification Checklist:

1. **CloudTrail**
   - [ ] Trail is logging
   - [ ] S3 bucket has logs
   - [ ] Log file validation enabled

2. **GuardDuty**
   - [ ] Service is enabled
   - [ ] No high-severity findings (or expected ones)
   - [ ] Email notifications working

3. **Security Hub**
   - [ ] Service is enabled
   - [ ] Security score visible
   - [ ] Findings are populating

4. **IAM Access Analyzer**
   - [ ] Analyzer is active
   - [ ] No unexpected external access

5. **CloudWatch Alarms**
   - [ ] Billing alarm created
   - [ ] SNS topic subscribed
   - [ ] Email confirmed

### Test Your Setup:

1. **Test GuardDuty** (Optional)
   - GuardDuty has sample findings you can generate
   - Go to GuardDuty → Settings → "Generate sample findings"
   - Check if you receive email notification

2. **Test CloudTrail**
   - Perform an action (create an S3 bucket)
   - Wait 15 minutes
   - Check CloudTrail logs in S3 bucket

---

## Monthly Maintenance Tasks

### Week 1:
- [ ] Review GuardDuty findings
- [ ] Check Security Hub compliance score
- [ ] Review IAM Access Analyzer findings

### Week 2:
- [ ] Review CloudTrail logs for unusual activity
- [ ] Check billing dashboard

### Week 3:
- [ ] Review Security Hub recommendations
- [ ] Update suppressed findings if needed

### Week 4:
- [ ] Review Trusted Advisor security checks
- [ ] Archive resolved findings
- [ ] Check S3 storage costs

---

## Cost Monitoring

### Set Up Cost Alerts:

1. **Go to Billing Dashboard**
   - AWS Console → "Billing and Cost Management"

2. **Create Budget**
   - Click "Budgets" → "Create budget"
   - Budget type: Cost budget
   - Amount: $30/month
   - Alert threshold: 80% ($24)
   - Email: your-email@example.com

3. **Monitor Service Costs**
   - Go to "Cost Explorer"
   - Filter by service:
     - CloudTrail
     - GuardDuty
     - Security Hub
     - S3 (for logs)

---

## Troubleshooting

### Issue: CloudTrail logs not appearing
- **Solution**: Wait 15 minutes, CloudTrail has a delay
- Check S3 bucket permissions
- Verify trail is enabled

### Issue: GuardDuty costs higher than expected
- **Solution**: Check if S3/EKS protection is enabled
- Review VPC Flow Logs volume
- Consider reducing log retention

### Issue: Security Hub showing too many findings
- **Solution**: Suppress non-critical findings
- Focus on HIGH and CRITICAL severity
- Disable unnecessary security standards

### Issue: Not receiving email notifications
- **Solution**: Check SNS subscription status
- Confirm email subscription
- Check spam folder

---

## Next Steps

Once comfortable with the Low Cost Plan:
1. Monitor costs for 1-2 months
2. Review security findings and value
3. Consider upgrading to Medium Cost Plan if needed
4. Add AWS Config for compliance tracking
5. Enable Inspector for vulnerability scanning

---

## Additional Resources

- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [CloudTrail Pricing](https://aws.amazon.com/cloudtrail/pricing/)
- [GuardDuty Pricing](https://aws.amazon.com/guardduty/pricing/)
- [Security Hub Pricing](https://aws.amazon.com/security-hub/pricing/)
