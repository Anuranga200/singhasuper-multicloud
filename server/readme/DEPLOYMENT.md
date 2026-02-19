# Singha Loyalty System - AWS Deployment Guide

## Architecture Overview

**Server-Based Architecture with ECS Fargate Spot + RDS MySQL**

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Users     │─────▶│     ALB      │─────▶│  ECS Fargate    │
│  (Browser)  │      │ (Port 80/443)│      │  Spot Instances │
└─────────────┘      └──────────────┘      └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │   RDS MySQL     │
                                            │   (db.t3.micro) │
                                            └─────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      CI/CD Pipeline                          │
│  GitHub → CodePipeline → CodeBuild → ECR → ECS Deploy       │
└─────────────────────────────────────────────────────────────┘
```

## Cost Breakdown (Monthly Estimates)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| **ECS Fargate Spot** | 2 tasks × 0.25 vCPU × 0.5GB | $5-8/month |
| **RDS MySQL** | db.t3.micro (20GB gp3) | $15-20/month |
| **Application Load Balancer** | 1 ALB | $16/month |
| **ECR** | Image storage | $1-2/month |
| **CodePipeline** | 1 pipeline | $1/month |
| **CodeBuild** | Build minutes | $2-5/month |
| **CloudWatch Logs** | 5GB retention | Free tier |
| **Data Transfer** | Moderate traffic | $5-10/month |
| **TOTAL** | | **$45-62/month** |

### Cost Optimization Tips:
- Use Fargate Spot (70% cheaper than on-demand)
- Single-AZ RDS for non-production (saves 50%)
- Enable RDS auto-pause for dev environments
- Use CloudFront for static assets (reduces ALB traffic)
- Set CloudWatch log retention to 7 days

---

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Docker** installed locally
4. **Git** and GitHub account
5. **Node.js 18+** for local development

---

## Deployment Steps

### Option 1: Quick Deploy (Automated Script)

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh production
```

The script will:
1. Create ECR repository
2. Build and push Docker image
3. Deploy CloudFormation stack (VPC, ECS, RDS, ALB)
4. Output API endpoint and RDS details

---

### Option 2: Manual Deployment

#### Step 1: Create ECR Repository

```bash
aws ecr create-repository \
    --repository-name singha-loyalty \
    --region us-east-1 \
    --image-scanning-configuration scanOnPush=true
```

#### Step 2: Build and Push Docker Image

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | \
docker login --username AWS --password-stdin \
<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build image
cd server
docker build -t singha-loyalty:latest .

# Tag and push
docker tag singha-loyalty:latest \
<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest

docker push \
<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest
```

#### Step 3: Deploy Infrastructure

```bash
aws cloudformation create-stack \
    --stack-name singha-loyalty-stack \
    --template-body file://infrastructure/cloudformation-ecs.yaml \
    --parameters \
        ParameterKey=ProjectName,ParameterValue=singha-loyalty \
        ParameterKey=Environment,ParameterValue=production \
        ParameterKey=DBPassword,ParameterValue=<YOUR_DB_PASSWORD> \
        ParameterKey=JWTSecret,ParameterValue=<YOUR_JWT_SECRET> \
        ParameterKey=ContainerImage,ParameterValue=<ECR_IMAGE_URI> \
    --capabilities CAPABILITY_IAM \
    --region us-east-1
```

Wait for stack creation (15-20 minutes):
```bash
aws cloudformation wait stack-create-complete \
    --stack-name singha-loyalty-stack \
    --region us-east-1
```

#### Step 4: Get Deployment Outputs

```bash
aws cloudformation describe-stacks \
    --stack-name singha-loyalty-stack \
    --query 'Stacks[0].Outputs' \
    --region us-east-1
```

#### Step 5: Run Database Migrations

Connect to RDS using MySQL client:

```bash
mysql -h <RDS_ENDPOINT> -u admin -p singha_loyalty < server/src/db/schema.sql
```

Or use AWS Systems Manager Session Manager to connect from a bastion host.

---

## CI/CD Pipeline Setup

### Deploy Pipeline

```bash
chmod +x infrastructure/deploy-pipeline.sh
./infrastructure/deploy-pipeline.sh
```

You'll need:
- GitHub repository (e.g., `username/singha-loyalty`)
- GitHub Personal Access Token with `repo` and `admin:repo_hook` permissions
- Branch name (default: `main`)

### Pipeline Flow

```
1. Developer pushes code to GitHub
   ↓
2. GitHub webhook triggers CodePipeline
   ↓
3. CodeBuild builds Docker image
   ↓
4. Image pushed to ECR
   ↓
5. ECS service updated with new image
   ↓
6. Rolling deployment (zero downtime)
```

### Manual Pipeline Trigger

```bash
aws codepipeline start-pipeline-execution \
    --name singha-loyalty-pipeline \
    --region us-east-1
```

---

## Environment Configuration

### Backend (.env)

```env
NODE_ENV=production
PORT=3000
CORS_ORIGIN=*

# RDS MySQL
DB_HOST=<RDS_ENDPOINT>
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=<YOUR_PASSWORD>
DB_NAME=singha_loyalty

# JWT
JWT_SECRET=<YOUR_JWT_SECRET>
JWT_REFRESH_SECRET=<YOUR_REFRESH_SECRET>

# AWS
AWS_REGION=us-east-1
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://<ALB_DNS>/api
VITE_AWS_REGION=us-east-1
```

---

## Monitoring & Logging

### CloudWatch Logs

```bash
# View ECS logs
aws logs tail /ecs/singha-loyalty --follow --region us-east-1
```

### ECS Service Status

```bash
aws ecs describe-services \
    --cluster singha-loyalty-cluster \
    --services singha-loyalty-service \
    --region us-east-1
```

### RDS Monitoring

```bash
# CPU utilization
aws cloudwatch get-metric-statistics \
    --namespace AWS/RDS \
    --metric-name CPUUtilization \
    --dimensions Name=DBInstanceIdentifier,Value=singha-loyalty-db \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --region us-east-1
```

---

## Scaling Configuration

### Auto Scaling (Optional)

Add to CloudFormation template:

```yaml
AutoScalingTarget:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Properties:
    MaxCapacity: 10
    MinCapacity: 2
    ResourceId: !Sub service/${ECSCluster}/${ECSService.Name}
    RoleARN: !GetAtt AutoScalingRole.Arn
    ScalableDimension: ecs:service:DesiredCount
    ServiceNamespace: ecs

AutoScalingPolicy:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    PolicyName: CPUScalingPolicy
    PolicyType: TargetTrackingScaling
    ScalingTargetId: !Ref AutoScalingTarget
    TargetTrackingScalingPolicyConfiguration:
      PredefinedMetricSpecification:
        PredefinedMetricType: ECSServiceAverageCPUUtilization
      TargetValue: 70.0
```

---

## Backup & Disaster Recovery

### RDS Automated Backups
- Retention: 7 days (configured in CloudFormation)
- Backup window: 03:00-04:00 UTC
- Maintenance window: Sunday 04:00-05:00 UTC

### Manual Snapshot

```bash
aws rds create-db-snapshot \
    --db-instance-identifier singha-loyalty-db \
    --db-snapshot-identifier singha-loyalty-manual-$(date +%Y%m%d) \
    --region us-east-1
```

### Restore from Snapshot

```bash
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier singha-loyalty-db-restored \
    --db-snapshot-identifier <SNAPSHOT_ID> \
    --region us-east-1
```

---

## Security Best Practices

1. **Secrets Management**
   - Store DB password in AWS Secrets Manager
   - Rotate credentials regularly
   - Use IAM roles instead of access keys

2. **Network Security**
   - RDS in private subnets (no public access)
   - Security groups with least privilege
   - Enable VPC Flow Logs

3. **Application Security**
   - Enable WAF on ALB (optional, adds cost)
   - Use HTTPS with ACM certificate
   - Implement rate limiting

4. **Monitoring**
   - Enable CloudTrail for audit logs
   - Set up CloudWatch alarms
   - Enable GuardDuty for threat detection

---

## Troubleshooting

### ECS Task Not Starting

```bash
# Check task status
aws ecs describe-tasks \
    --cluster singha-loyalty-cluster \
    --tasks <TASK_ARN> \
    --region us-east-1

# Check logs
aws logs tail /ecs/singha-loyalty --follow
```

### Database Connection Issues

```bash
# Test from ECS task
aws ecs execute-command \
    --cluster singha-loyalty-cluster \
    --task <TASK_ID> \
    --container singha-loyalty-container \
    --interactive \
    --command "/bin/sh"

# Inside container
nc -zv <RDS_ENDPOINT> 3306
```

### High Costs

```bash
# Check cost breakdown
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=SERVICE
```

---

## Cleanup

### Delete All Resources

```bash
# Delete pipeline stack
aws cloudformation delete-stack \
    --stack-name singha-loyalty-pipeline \
    --region us-east-1

# Delete main stack
aws cloudformation delete-stack \
    --stack-name singha-loyalty-stack \
    --region us-east-1

# Delete ECR images
aws ecr batch-delete-image \
    --repository-name singha-loyalty \
    --image-ids imageTag=latest \
    --region us-east-1

# Delete ECR repository
aws ecr delete-repository \
    --repository-name singha-loyalty \
    --force \
    --region us-east-1
```

---

## Support & Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **ECS Best Practices**: https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/
- **RDS MySQL Guide**: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/

---

## Next Steps

1. ✅ Deploy infrastructure
2. ✅ Run database migrations
3. ✅ Set up CI/CD pipeline
4. 🔲 Configure custom domain with Route 53
5. 🔲 Add SSL certificate with ACM
6. 🔲 Deploy frontend to S3 + CloudFront
7. 🔲 Set up monitoring alerts
8. 🔲 Configure auto-scaling
9. 🔲 Enable WAF for security
10. 🔲 Set up backup automation
