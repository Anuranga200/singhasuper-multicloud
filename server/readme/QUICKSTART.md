# Quick Start Guide - Singha Loyalty System

Get your Singha Loyalty System deployed to AWS in under 30 minutes!

## Prerequisites Checklist

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker installed locally
- [ ] Git repository (GitHub recommended)
- [ ] Node.js 18+ installed

## 🚀 Deployment in 5 Steps

### Step 1: Clone and Prepare (2 minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd singha-loyalty-system

# Make deployment scripts executable
chmod +x deploy.sh
chmod +x infrastructure/deploy-pipeline.sh
```

### Step 2: Deploy Infrastructure (15 minutes)

```bash
# Run automated deployment
./deploy.sh production
```

**You'll be prompted for:**
- Database password (min 8 characters)
- JWT secret key (random string)

**What happens:**
1. Creates ECR repository
2. Builds Docker image
3. Pushes image to ECR
4. Deploys CloudFormation stack:
   - VPC with public/private subnets
   - Application Load Balancer
   - ECS Fargate cluster with Spot instances
   - RDS MySQL database
   - Security groups
   - IAM roles

**Wait time:** 15-20 minutes for stack creation

### Step 3: Initialize Database (3 minutes)

After deployment completes, you'll see the RDS endpoint. Connect and run migrations:

```bash
# Get RDS endpoint from output
RDS_ENDPOINT="<from-deployment-output>"

# Run migration
mysql -h $RDS_ENDPOINT -u admin -p singha_loyalty < server/src/db/schema.sql
```

**Alternative:** Use MySQL Workbench or any MySQL client.

### Step 4: Test Your API (2 minutes)

```bash
# Get ALB endpoint from deployment output
ALB_ENDPOINT="<from-deployment-output>"

# Test health check
curl http://$ALB_ENDPOINT/health

# Test customer registration
curl -X POST http://$ALB_ENDPOINT/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "nicNumber": "123456789V",
    "fullName": "Test Customer",
    "phoneNumber": "0771234567"
  }'

# Test admin login
curl -X POST http://$ALB_ENDPOINT/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@singha.com",
    "password": "Admin@123"
  }'
```

### Step 5: Setup CI/CD Pipeline (5 minutes)

```bash
# Deploy pipeline
./infrastructure/deploy-pipeline.sh
```

**You'll be prompted for:**
- GitHub repository (username/repo)
- GitHub branch (default: main)
- GitHub Personal Access Token

**Create GitHub Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` and `admin:repo_hook`
4. Copy token

**What happens:**
- Creates CodePipeline
- Creates CodeBuild project
- Sets up GitHub webhook
- Configures automatic deployments

---

## 🎉 You're Done!

Your system is now deployed and running!

### Access Your Application

**Backend API:**
```
http://<ALB_ENDPOINT>/api
```

**Health Check:**
```
http://<ALB_ENDPOINT>/health
```

### Update Frontend Configuration

Edit your frontend `.env` file:

```env
VITE_API_BASE_URL=http://<ALB_ENDPOINT>/api
```

Then build and deploy frontend:

```bash
npm run build
# Deploy to S3/CloudFront or serve from Express
```

---

## 📊 Verify Deployment

### Check ECS Service

```bash
aws ecs describe-services \
  --cluster singha-loyalty-cluster \
  --services singha-loyalty-service \
  --region us-east-1
```

Look for:
- `runningCount: 2` (2 tasks running)
- `desiredCount: 2`
- `status: ACTIVE`

### Check RDS Status

```bash
aws rds describe-db-instances \
  --db-instance-identifier singha-loyalty-db \
  --region us-east-1 \
  --query 'DBInstances[0].DBInstanceStatus'
```

Should return: `"available"`

### View Logs

```bash
# Real-time logs
aws logs tail /ecs/singha-loyalty --follow --region us-east-1

# Last 100 lines
aws logs tail /ecs/singha-loyalty --since 1h --region us-east-1
```

---

## 🔧 Common Issues & Solutions

### Issue: Stack creation failed

**Solution:**
```bash
# Check stack events
aws cloudformation describe-stack-events \
  --stack-name singha-loyalty-stack \
  --region us-east-1 \
  --max-items 20

# Delete failed stack and retry
aws cloudformation delete-stack \
  --stack-name singha-loyalty-stack \
  --region us-east-1
```

### Issue: ECS tasks not starting

**Solution:**
```bash
# Check task status
aws ecs list-tasks \
  --cluster singha-loyalty-cluster \
  --region us-east-1

# Get task details
aws ecs describe-tasks \
  --cluster singha-loyalty-cluster \
  --tasks <TASK_ARN> \
  --region us-east-1

# Common causes:
# - Image pull error (check ECR permissions)
# - Health check failing (check /health endpoint)
# - Environment variables missing
```

### Issue: Cannot connect to RDS

**Solution:**
```bash
# Verify security group allows ECS → RDS
# Check RDS is in private subnet
# Verify DB credentials in task definition

# Test from ECS task
aws ecs execute-command \
  --cluster singha-loyalty-cluster \
  --task <TASK_ID> \
  --container singha-loyalty-container \
  --interactive \
  --command "/bin/sh"

# Inside container:
nc -zv <RDS_ENDPOINT> 3306
```

### Issue: High costs

**Solution:**
```bash
# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost

# Optimization tips:
# 1. Ensure Fargate Spot is being used (check ECS service)
# 2. Reduce RDS instance size if underutilized
# 3. Set CloudWatch log retention to 7 days
# 4. Delete unused ECR images
# 5. Enable RDS auto-pause for dev environments
```

---

## 🔄 Making Updates

### Update Application Code

```bash
# Commit and push to GitHub
git add .
git commit -m "Update feature"
git push origin main

# Pipeline automatically:
# 1. Builds new Docker image
# 2. Pushes to ECR
# 3. Updates ECS service
# 4. Performs rolling deployment
```

### Manual Deployment

```bash
# Build and push image
cd server
docker build -t singha-loyalty:latest .
docker tag singha-loyalty:latest <ECR_URI>:latest
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ECR_URI>
docker push <ECR_URI>:latest

# Force new deployment
aws ecs update-service \
  --cluster singha-loyalty-cluster \
  --service singha-loyalty-service \
  --force-new-deployment \
  --region us-east-1
```

### Update Infrastructure

```bash
# Modify infrastructure/cloudformation-ecs.yaml
# Then update stack
aws cloudformation update-stack \
  --stack-name singha-loyalty-stack \
  --template-body file://infrastructure/cloudformation-ecs.yaml \
  --parameters <same-as-before> \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

---

## 📈 Monitoring

### CloudWatch Dashboard

Create a custom dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name singha-loyalty \
  --dashboard-body file://dashboard.json
```

### Set Up Alarms

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
```

---

## 🧹 Cleanup

### Delete Everything

```bash
# Delete pipeline stack
aws cloudformation delete-stack \
  --stack-name singha-loyalty-pipeline \
  --region us-east-1

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name singha-loyalty-pipeline \
  --region us-east-1

# Delete main stack
aws cloudformation delete-stack \
  --stack-name singha-loyalty-stack \
  --region us-east-1

# Wait for deletion (takes 10-15 minutes)
aws cloudformation wait stack-delete-complete \
  --stack-name singha-loyalty-stack \
  --region us-east-1

# Delete ECR images and repository
aws ecr batch-delete-image \
  --repository-name singha-loyalty \
  --image-ids imageTag=latest \
  --region us-east-1

aws ecr delete-repository \
  --repository-name singha-loyalty \
  --force \
  --region us-east-1

# Verify all resources deleted
aws cloudformation list-stacks \
  --stack-status-filter DELETE_COMPLETE \
  --region us-east-1
```

**Cost after cleanup:** $0 (all resources deleted)

---

## 📚 Next Steps

1. **Add Custom Domain**
   - Register domain in Route 53
   - Create SSL certificate in ACM
   - Update ALB listener for HTTPS

2. **Deploy Frontend**
   - Build React app: `npm run build`
   - Upload to S3: `aws s3 sync dist/ s3://your-bucket`
   - Create CloudFront distribution

3. **Enable Auto-Scaling**
   - Add auto-scaling policies to CloudFormation
   - Set target CPU utilization (70%)
   - Configure min/max task count

4. **Add Monitoring**
   - Create CloudWatch dashboard
   - Set up SNS alerts
   - Enable X-Ray tracing

5. **Implement Caching**
   - Add Redis (ElastiCache)
   - Cache frequent queries
   - Reduce database load

6. **Security Hardening**
   - Enable WAF on ALB
   - Implement rate limiting
   - Add Secrets Manager for credentials
   - Enable GuardDuty

---

## 🆘 Getting Help

- **AWS Documentation**: https://docs.aws.amazon.com/
- **ECS Troubleshooting**: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/troubleshooting.html
- **RDS Best Practices**: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html

---

## 💰 Cost Estimate

**Monthly costs for this setup:**
- ECS Fargate Spot: $5-8
- RDS MySQL (db.t3.micro): $15-20
- Application Load Balancer: $16
- ECR + CodePipeline + Misc: $5-10
- **Total: $45-62/month**

**Free tier eligible:**
- First 12 months: Some RDS and ECS usage free
- Always free: CloudWatch (basic), CodeBuild (100 minutes/month)

---

## ✅ Success Checklist

- [ ] Infrastructure deployed successfully
- [ ] Database migrations completed
- [ ] API health check returns 200
- [ ] Customer registration works
- [ ] Admin login works
- [ ] CI/CD pipeline configured
- [ ] Logs visible in CloudWatch
- [ ] Frontend connected to backend
- [ ] Monitoring alarms set up
- [ ] Backup strategy configured

**Congratulations! Your Singha Loyalty System is live! 🎉**
