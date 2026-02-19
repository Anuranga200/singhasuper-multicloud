# Singha Loyalty System - Deployment Documentation

## 📚 Complete Documentation Index

Welcome! This project has been transformed from serverless to server-based architecture and is ready for deployment.

---

## 🚀 Quick Start

**New to AWS?** Start here:
1. **START_HERE.md** - Overview and options
2. **CONSOLE_DEPLOYMENT_GUIDE.md** - Step-by-step AWS Console guide (RECOMMENDED FOR LEARNING)
3. **VISUAL_GUIDE.md** - Visual diagrams of how services connect

**Want to deploy quickly?**
1. **NEXT_STEPS.md** - Quick deployment with scripts
2. Run: `./deploy.sh production`

---

## 📖 Documentation Structure

### 🎯 Getting Started (Read First)

| Document | Purpose | Time | Audience |
|----------|---------|------|----------|
| **START_HERE.md** | Overview & options | 5 min | Everyone |
| **PROJECT_TRANSFORMATION.md** | What changed | 10 min | Understanding context |
| **VISUAL_GUIDE.md** | Service diagrams | 10 min | Visual learners |

### 🔧 Deployment Guides (Choose One)

| Document | Method | Time | Best For |
|----------|--------|------|----------|
| **CONSOLE_DEPLOYMENT_GUIDE.md** | AWS Console | 2-3 hrs | Learning AWS deeply ⭐ |
| **NEXT_STEPS.md** | Scripts | 1 hr | Quick deployment |
| **COMPLETION_CHECKLIST.md** | Detailed steps | 1.5 hrs | Thorough approach |

### 📚 Reference Documentation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **ARCHITECTURE.md** | System architecture | Understanding design |
| **DEPLOYMENT.md** | Comprehensive guide | Troubleshooting |
| **QUICKSTART.md** | Quick reference | After deployment |
| **server/README.md** | Backend docs | Development |

---

## 🎓 Learning Path

### Path 1: Deep Understanding (Recommended for First-Time)

```
1. START_HERE.md (5 min)
   ↓
2. VISUAL_GUIDE.md (10 min)
   ↓
3. CONSOLE_DEPLOYMENT_GUIDE.md (2-3 hours)
   ↓
4. Deploy using AWS Console
   ↓
5. Understand every service connection
```

**Why:** You'll learn AWS services deeply and understand how they interconnect.

### Path 2: Quick Deployment

```
1. START_HERE.md (5 min)
   ↓
2. NEXT_STEPS.md (5 min)
   ↓
3. Run ./deploy.sh production (30 min)
   ↓
4. Application deployed
```

**Why:** Fastest way to get running.

### Path 3: Balanced Approach

```
1. START_HERE.md (5 min)
   ↓
2. VISUAL_GUIDE.md (10 min)
   ↓
3. Test locally (NEXT_STEPS.md Option 3) (15 min)
   ↓
4. Deploy with scripts (30 min)
   ↓
5. Review CONSOLE_DEPLOYMENT_GUIDE.md to understand
```

**Why:** Balance between speed and understanding.

---

## 🏗️ Architecture Overview

### Before (Serverless)
```
React → API Gateway → Lambda Functions → DynamoDB
```

### After (Server-Based)
```
React → ALB → ECS Fargate Spot → RDS MySQL
                ↑
               ECR
                ↑
        CodePipeline → CodeBuild
                ↑
              GitHub
```

### Key Benefits
- ✅ 70% cost savings with Spot instances
- ✅ No cold starts
- ✅ Traditional database (ACID, JOINs)
- ✅ Full server control
- ✅ Easier debugging

---

## 💰 Cost Breakdown

**Monthly Estimate: $45-62**

| Service | Configuration | Cost |
|---------|--------------|------|
| ECS Fargate Spot | 2 tasks × 0.25 vCPU × 0.5GB | $5-8 |
| RDS MySQL | db.t3.micro, 20GB | $15-20 |
| Application Load Balancer | 1 ALB | $16 |
| ECR + CodePipeline | Image storage + CI/CD | $3-7 |
| CloudWatch | Logs + Metrics | $5-10 |
| Data Transfer | Moderate traffic | $5-10 |

---

## 🎯 Deployment Options Comparison

### Option 1: AWS Console (CONSOLE_DEPLOYMENT_GUIDE.md)

**Pros:**
- ✅ Learn AWS services deeply
- ✅ Understand service connections
- ✅ Visual interface
- ✅ Step-by-step guidance
- ✅ Best for first-time AWS users

**Cons:**
- ⏱️ Takes 2-3 hours
- 🔄 Manual steps
- 📝 More clicking

**Best for:** Learning, understanding, first deployment

---

### Option 2: Automated Scripts (NEXT_STEPS.md)

**Pros:**
- ⚡ Fast (30 minutes)
- 🤖 Automated
- ✅ Repeatable
- 📦 Infrastructure as Code

**Cons:**
- 🎓 Less learning
- 🔍 Harder to troubleshoot
- 📚 Need to understand CloudFormation

**Best for:** Quick deployment, experienced users, CI/CD

---

### Option 3: Detailed Checklist (COMPLETION_CHECKLIST.md)

**Pros:**
- ✅ Comprehensive
- 📋 Organized
- 🔍 Verification steps
- 📊 Testing included

**Cons:**
- ⏱️ Takes 1.5 hours
- 📝 Many steps
- 🔄 Mix of console and CLI

**Best for:** Thorough deployment, production environments

---

## 🔑 Prerequisites

### Required
- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured
- [ ] Docker installed and running
- [ ] Node.js 18+ installed
- [ ] Git repository (for CI/CD)

### Recommended
- [ ] MySQL client (for database access)
- [ ] Postman or curl (for API testing)
- [ ] Basic AWS knowledge
- [ ] Basic Docker knowledge

### Check Prerequisites
```bash
# AWS CLI
aws --version
aws sts get-caller-identity

# Docker
docker --version
docker ps

# Node.js
node --version
npm --version

# Git
git --version
```

---

## 📊 What Gets Deployed

### Infrastructure
- ✅ VPC with public/private subnets
- ✅ Internet Gateway
- ✅ Security Groups (ALB, ECS, RDS)
- ✅ Application Load Balancer
- ✅ Target Group
- ✅ RDS MySQL database
- ✅ ECS Fargate cluster
- ✅ ECS service with 2 tasks
- ✅ ECR repository
- ✅ CloudWatch log groups
- ✅ IAM roles and policies

### Application
- ✅ Express.js server (containerized)
- ✅ MySQL database schema
- ✅ Admin user (seeded)
- ✅ Sample customers (optional)

### CI/CD (Optional)
- ✅ CodePipeline
- ✅ CodeBuild project
- ✅ GitHub webhook
- ✅ Automated deployments

---

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl http://[ALB-DNS]/health
```
Expected: `{"status":"healthy",...}`

### 2. Customer Registration
```bash
curl -X POST http://[ALB-DNS]/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "nicNumber": "123456789V",
    "fullName": "Test User",
    "phoneNumber": "0771234567"
  }'
```

### 3. Admin Login
```bash
curl -X POST http://[ALB-DNS]/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@singha.com",
    "password": "Admin@123"
  }'
```

### 4. Get Customers (Protected)
```bash
TOKEN="[your-jwt-token]"
curl http://[ALB-DNS]/api/customers \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🆘 Troubleshooting

### Common Issues

**Issue: AWS CLI not configured**
```bash
aws configure
# Enter your credentials
```

**Issue: Docker not running**
```bash
# Windows/Mac: Start Docker Desktop
# Linux: sudo systemctl start docker
```

**Issue: ECS tasks not starting**
- Check CloudWatch logs: `/ecs/singha-loyalty`
- Verify environment variables in task definition
- Check security group rules

**Issue: Database connection failed**
- Verify RDS endpoint in task definition
- Check RDS security group allows ECS
- Verify database credentials

**Issue: 503 from ALB**
- Check target group health
- Verify ECS tasks are running
- Check health check configuration

### Where to Get Help

1. **DEPLOYMENT.md** - Comprehensive troubleshooting
2. **CONSOLE_DEPLOYMENT_GUIDE.md** - Step-by-step verification
3. **CloudWatch Logs** - Application logs
4. **AWS Support** - https://console.aws.amazon.com/support/

---

## 📈 After Deployment

### Immediate (Day 1)
- [ ] Test all API endpoints
- [ ] Monitor CloudWatch logs
- [ ] Verify costs in AWS Console
- [ ] Change default admin password
- [ ] Set up billing alerts

### Short-term (Week 1)
- [ ] Add custom domain (Route 53)
- [ ] Enable HTTPS (ACM certificate)
- [ ] Deploy frontend to S3/CloudFront
- [ ] Set up monitoring alerts
- [ ] Review security groups

### Long-term (Month 1)
- [ ] Configure auto-scaling
- [ ] Set up automated backups
- [ ] Implement caching (Redis)
- [ ] Security audit
- [ ] Performance optimization

---

## 🎓 Learning Resources

### AWS Services Documentation
- **VPC**: https://docs.aws.amazon.com/vpc/
- **ECS**: https://docs.aws.amazon.com/ecs/
- **RDS**: https://docs.aws.amazon.com/rds/
- **ALB**: https://docs.aws.amazon.com/elasticloadbalancing/
- **ECR**: https://docs.aws.amazon.com/ecr/
- **CodePipeline**: https://docs.aws.amazon.com/codepipeline/

### Tutorials
- AWS ECS Workshop: https://ecsworkshop.com/
- AWS Well-Architected: https://aws.amazon.com/architecture/well-architected/

---

## 🎯 Recommended Deployment Path

### For Beginners
```
1. Read START_HERE.md
2. Read VISUAL_GUIDE.md
3. Follow CONSOLE_DEPLOYMENT_GUIDE.md
4. Deploy using AWS Console
5. Learn each service
```

### For Experienced Users
```
1. Read START_HERE.md
2. Review ARCHITECTURE.md
3. Run ./deploy.sh production
4. Verify deployment
```

### For Production
```
1. Test locally first
2. Deploy to dev environment
3. Follow COMPLETION_CHECKLIST.md
4. Set up monitoring
5. Deploy to production
6. Configure CI/CD
```

---

## ✅ Success Criteria

Your deployment is successful when:

✅ All infrastructure deployed
✅ ECS tasks running and healthy
✅ RDS database accessible
✅ Health check returns 200
✅ Customer registration works
✅ Admin login works
✅ Protected endpoints require JWT
✅ Logs visible in CloudWatch
✅ Costs within budget

---

## 📞 Quick Reference

| Need | Document |
|------|----------|
| Start deployment | START_HERE.md |
| Learn AWS services | CONSOLE_DEPLOYMENT_GUIDE.md |
| Visual diagrams | VISUAL_GUIDE.md |
| Quick deploy | NEXT_STEPS.md |
| Troubleshooting | DEPLOYMENT.md |
| Architecture details | ARCHITECTURE.md |
| Backend info | server/README.md |

---

## 🎉 Ready to Deploy!

Choose your path and get started:

1. **Learn deeply**: CONSOLE_DEPLOYMENT_GUIDE.md
2. **Deploy quickly**: NEXT_STEPS.md
3. **Understand visually**: VISUAL_GUIDE.md

**Estimated time to production: 1-3 hours**

Good luck! 🚀

---

**Last Updated:** January 31, 2026
**Status:** Ready for Deployment
**Architecture:** Server-Based (ECS + RDS)
**Estimated Cost:** $45-62/month
