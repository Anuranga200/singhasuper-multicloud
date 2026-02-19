# Deployment Completion Checklist

## ✅ Pre-Deployment Checklist

### 1. AWS Account Setup
- [ ] AWS account created and configured
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Verify account access: `aws sts get-caller-identity`

### 2. Local Environment
- [ ] Docker installed and running
- [ ] Node.js 18+ installed
- [ ] Git repository initialized
- [ ] GitHub repository created (for CI/CD)

### 3. Configuration Files
- [ ] Update `server/.env` with your values
- [ ] Update `.env` in root with frontend API URL
- [ ] Generate strong JWT secrets
- [ ] Choose secure database password

## 🚀 Deployment Steps

### Step 1: Deploy Infrastructure (20 minutes)

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh production
```

**What to provide:**
- Database password (min 8 characters, secure)
- JWT secret (random string, 32+ characters)

**Expected output:**
- ✅ ECR repository created
- ✅ Docker image built and pushed
- ✅ CloudFormation stack deployed
- ✅ ALB endpoint URL
- ✅ RDS endpoint URL

**Checklist:**
- [ ] Script completed without errors
- [ ] Note down ALB endpoint: `_________________`
- [ ] Note down RDS endpoint: `_________________`
- [ ] Verify ECS service running: `aws ecs describe-services --cluster singha-loyalty-cluster --services singha-loyalty-service`

### Step 2: Initialize Database (5 minutes)

```bash
# Connect to RDS
mysql -h <RDS_ENDPOINT> -u admin -p

# Run migrations
source server/src/db/schema.sql

# Seed initial data
npm run seed --prefix server
```

**Checklist:**
- [ ] Database schema created
- [ ] Admin user created (admin@singha.com / Admin@123)
- [ ] Sample customers created
- [ ] Verify tables: `SHOW TABLES;`

### Step 3: Test API (5 minutes)

```bash
# Set your ALB endpoint
export API_URL="http://<ALB_ENDPOINT>"

# Test health check
curl $API_URL/health

# Test customer registration
curl -X POST $API_URL/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "nicNumber": "999888777V",
    "fullName": "Test User",
    "phoneNumber": "0771112222"
  }'

# Test admin login
curl -X POST $API_URL/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@singha.com",
    "password": "Admin@123"
  }'

# Save the token from response
export TOKEN="<your-jwt-token>"

# Test protected endpoint
curl $API_URL/api/customers \
  -H "Authorization: Bearer $TOKEN"
```

**Checklist:**
- [ ] Health check returns 200
- [ ] Customer registration works
- [ ] Admin login returns JWT token
- [ ] Protected endpoint accessible with token

### Step 4: Setup CI/CD Pipeline (10 minutes)

```bash
# Make script executable
chmod +x infrastructure/deploy-pipeline.sh

# Deploy pipeline
./infrastructure/deploy-pipeline.sh
```

**What to provide:**
- GitHub repository (username/repo)
- GitHub branch (main)
- GitHub Personal Access Token

**Create GitHub Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` and `admin:repo_hook`
4. Copy token (save it securely!)

**Checklist:**
- [ ] Pipeline stack deployed
- [ ] GitHub webhook created
- [ ] Test pipeline: Make a commit and push
- [ ] Verify pipeline execution in AWS Console

### Step 5: Update Frontend (5 minutes)

```bash
# Update frontend .env
echo "VITE_API_BASE_URL=http://<ALB_ENDPOINT>/api" > .env

# Build frontend
npm run build

# Test locally
npm run preview
```

**Checklist:**
- [ ] Frontend .env updated
- [ ] Build successful
- [ ] Frontend can connect to backend
- [ ] Registration form works
- [ ] Admin login works

## 🔒 Security Hardening

### Immediate Actions
- [ ] Change default admin password
- [ ] Generate new JWT secrets (production)
- [ ] Update RDS password
- [ ] Enable MFA on AWS account
- [ ] Restrict security group rules

### Recommended Actions
- [ ] Add SSL certificate (ACM)
- [ ] Enable HTTPS on ALB
- [ ] Add custom domain (Route 53)
- [ ] Enable WAF on ALB
- [ ] Set up CloudWatch alarms
- [ ] Enable AWS GuardDuty
- [ ] Configure backup notifications

## 📊 Monitoring Setup

### CloudWatch Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name singha-ecs-high-cpu \
  --alarm-description "ECS CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=singha-loyalty-service \
               Name=ClusterName,Value=singha-loyalty-cluster

# RDS high CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name singha-rds-high-cpu \
  --alarm-description "RDS CPU > 90%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 90 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=DBInstanceIdentifier,Value=singha-loyalty-db
```

**Checklist:**
- [ ] ECS CPU alarm created
- [ ] RDS CPU alarm created
- [ ] ALB 5XX error alarm created
- [ ] SNS topic for notifications created

## 🧪 Testing Checklist

### Functional Testing
- [ ] Customer registration works
- [ ] Duplicate NIC validation works
- [ ] Admin login works
- [ ] JWT token refresh works
- [ ] Customer list retrieval works
- [ ] Customer deletion works
- [ ] Health check endpoint works

### Load Testing (Optional)
```bash
# Install Apache Bench
# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 http://<ALB_ENDPOINT>/health
```

- [ ] Health check handles load
- [ ] API responds within 500ms
- [ ] No 5XX errors under load

### Security Testing
- [ ] SQL injection attempts blocked
- [ ] XSS attempts blocked
- [ ] Invalid JWT tokens rejected
- [ ] Expired tokens rejected
- [ ] CORS configured correctly

## 📝 Documentation

- [ ] Update README with deployment info
- [ ] Document API endpoints
- [ ] Create runbook for common issues
- [ ] Document backup/restore procedures
- [ ] Create incident response plan

## 🎯 Post-Deployment

### Day 1
- [ ] Monitor CloudWatch logs
- [ ] Check ECS task health
- [ ] Verify RDS connections
- [ ] Test all API endpoints
- [ ] Monitor costs in AWS Cost Explorer

### Week 1
- [ ] Review CloudWatch metrics
- [ ] Optimize resource allocation
- [ ] Set up automated backups
- [ ] Configure log retention
- [ ] Review security groups

### Month 1
- [ ] Analyze cost trends
- [ ] Review performance metrics
- [ ] Plan scaling strategy
- [ ] Update documentation
- [ ] Conduct security audit

## 🆘 Troubleshooting

### ECS Tasks Not Starting
```bash
# Check task status
aws ecs describe-tasks \
  --cluster singha-loyalty-cluster \
  --tasks $(aws ecs list-tasks --cluster singha-loyalty-cluster --query 'taskArns[0]' --output text)

# Check logs
aws logs tail /ecs/singha-loyalty --follow
```

### Database Connection Issues
```bash
# Test from local machine (if RDS is public)
mysql -h <RDS_ENDPOINT> -u admin -p

# Check security groups
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=*singha*"
```

### Pipeline Failures
```bash
# Check build logs
aws codebuild batch-get-builds \
  --ids $(aws codebuild list-builds-for-project \
    --project-name singha-loyalty-build \
    --query 'ids[0]' --output text)
```

## 💰 Cost Monitoring

### Daily Cost Check
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

**Expected Monthly Cost:** $45-62

**Cost Breakdown:**
- ECS Fargate Spot: $5-8
- RDS MySQL: $15-20
- ALB: $16
- Other: $10-18

## ✅ Final Verification

- [ ] All services running
- [ ] API accessible via ALB
- [ ] Database populated
- [ ] CI/CD pipeline working
- [ ] Monitoring configured
- [ ] Backups enabled
- [ ] Documentation updated
- [ ] Team trained
- [ ] Costs within budget

## 🎉 Deployment Complete!

Congratulations! Your Singha Loyalty System is now live on AWS with:
- ✅ High availability (Multi-AZ)
- ✅ Auto-scaling (ECS Fargate)
- ✅ Automated deployments (CI/CD)
- ✅ Cost-optimized (Spot instances)
- ✅ Production-ready infrastructure

**Next Steps:**
1. Add custom domain
2. Enable HTTPS
3. Deploy frontend to S3/CloudFront
4. Set up monitoring alerts
5. Plan for scaling

---

**Support Resources:**
- AWS Documentation: https://docs.aws.amazon.com/
- Project Documentation: See ARCHITECTURE.md, DEPLOYMENT.md
- Troubleshooting: See QUICKSTART.md

**Emergency Contacts:**
- AWS Support: https://console.aws.amazon.com/support/
- DevOps Team: [Add your team contact]
