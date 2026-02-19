# Singha Loyalty System - Architecture Documentation

## Overview

The Singha Loyalty System has been transformed from a **serverless architecture** (Lambda + DynamoDB) to a **server-based architecture** (ECS Fargate + RDS MySQL) for better control, cost optimization with Spot instances, and traditional database benefits.

## Architecture Comparison

### Before (Serverless)
```
React Frontend → API Gateway → Lambda Functions → DynamoDB
```

### After (Server-Based)
```
React Frontend → ALB → ECS Fargate Spot → RDS MySQL
                                ↓
                              ECR (Docker Images)
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   CloudFront   │ (Optional - Frontend)
                    │   + S3 Bucket  │
                    └────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                         AWS VPC (10.0.0.0/16)                   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Public Subnets (2 AZs)                       │  │
│  │                                                            │  │
│  │  ┌─────────────────────┐                                  │  │
│  │  │ Application Load    │                                  │  │
│  │  │ Balancer (ALB)      │                                  │  │
│  │  │ - Port 80/443       │                                  │  │
│  │  │ - Health checks     │                                  │  │
│  │  └──────────┬──────────┘                                  │  │
│  │             │                                              │  │
│  │             ▼                                              │  │
│  │  ┌─────────────────────┐    ┌─────────────────────┐      │  │
│  │  │  ECS Fargate Task   │    │  ECS Fargate Task   │      │  │
│  │  │  (Spot Instance)    │    │  (Spot Instance)    │      │  │
│  │  │  - 0.25 vCPU        │    │  - 0.25 vCPU        │      │  │
│  │  │  - 512 MB RAM       │    │  - 512 MB RAM       │      │  │
│  │  │  - Node.js Server   │    │  - Node.js Server   │      │  │
│  │  └──────────┬──────────┘    └──────────┬──────────┘      │  │
│  └─────────────┼────────────────────────────┼───────────────┘  │
│                │                            │                   │
│                └────────────┬───────────────┘                   │
│                             │                                   │
│  ┌─────────────────────────▼────────────────────────────────┐  │
│  │              Private Subnets (2 AZs)                      │  │
│  │                                                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │         RDS MySQL (db.t3.micro)                     │  │  │
│  │  │         - Multi-AZ: Optional                        │  │  │
│  │  │         - Storage: 20GB gp3                         │  │  │
│  │  │         - Automated backups: 7 days                 │  │  │
│  │  │         - Encryption: Enabled                       │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                      CI/CD Pipeline                             │
│                                                                  │
│  GitHub → CodePipeline → CodeBuild → ECR → ECS Deploy          │
│                                                                  │
│  1. Code push triggers webhook                                  │
│  2. CodeBuild builds Docker image                               │
│  3. Image pushed to ECR                                         │
│  4. ECS service updated (rolling deployment)                    │
└────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React + Vite)

**Technology Stack:**
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS + Shadcn/ui
- React Router for navigation
- React Query for data fetching

**Deployment Options:**
- **Option A**: S3 + CloudFront (Static hosting)
- **Option B**: Serve from Express server
- **Option C**: Netlify/Vercel (External hosting)

**Key Features:**
- Customer registration form
- Admin dashboard
- JWT token management
- Automatic token refresh

### 2. Backend (Express.js Server)

**Technology Stack:**
- Node.js 18 (Alpine Linux)
- Express.js framework
- MySQL2 for database
- JWT for authentication
- Helmet for security
- Morgan for logging

**API Endpoints:**
```
Public:
  GET  /health                    - Health check
  POST /api/customers/register    - Register customer

Protected (JWT required):
  POST   /api/admin/login         - Admin login
  POST   /api/admin/refresh       - Refresh token
  GET    /api/customers           - List customers
  DELETE /api/customers/:id       - Delete customer
```

**Container Specifications:**
- Base image: node:18-alpine
- Size: ~150MB (optimized)
- Non-root user: nodejs (UID 1001)
- Health check: /health endpoint
- Graceful shutdown: SIGTERM handling

### 3. Database (RDS MySQL)

**Schema:**

```sql
-- Admins table
CREATE TABLE admins (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP NULL,
  INDEX idx_email (email)
);

-- Customers table
CREATE TABLE customers (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nic_number VARCHAR(20) NOT NULL UNIQUE,
  full_name VARCHAR(100) NOT NULL,
  phone_number VARCHAR(20) NOT NULL,
  loyalty_number VARCHAR(10) NOT NULL UNIQUE,
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_deleted TINYINT(1) DEFAULT 0,
  deleted_at TIMESTAMP NULL,
  deleted_by VARCHAR(255) NULL,
  INDEX idx_phone (phone_number),
  INDEX idx_deleted (is_deleted)
);
```

**Configuration:**
- Engine: MySQL 8.0.35
- Instance: db.t3.micro (1 vCPU, 1GB RAM)
- Storage: 20GB gp3 (3000 IOPS)
- Backup: 7-day retention
- Encryption: AES-256
- Multi-AZ: Optional (production)

### 4. Load Balancer (ALB)

**Configuration:**
- Type: Application Load Balancer
- Scheme: Internet-facing
- Listeners: HTTP (80), HTTPS (443)
- Target: ECS tasks (port 3000)
- Health check: GET /health every 30s

**Features:**
- Cross-zone load balancing
- Connection draining
- Sticky sessions (optional)
- SSL termination (with ACM)

### 5. Container Orchestration (ECS Fargate)

**Cluster Configuration:**
- Capacity providers: FARGATE + FARGATE_SPOT
- Strategy: 80% Spot, 20% On-Demand
- Container Insights: Enabled

**Task Definition:**
- CPU: 256 units (0.25 vCPU)
- Memory: 512 MB
- Network mode: awsvpc
- Launch type: FARGATE

**Service Configuration:**
- Desired count: 2 tasks
- Deployment: Rolling update
- Min healthy: 50%
- Max percent: 200%
- Circuit breaker: Enabled

**Cost Savings with Spot:**
- Spot discount: ~70% vs On-Demand
- Interruption handling: Automatic task replacement
- Recommended for: Non-critical workloads

### 6. Container Registry (ECR)

**Configuration:**
- Image scanning: Enabled
- Lifecycle policy: Keep last 10 images
- Encryption: AES-256
- Tag immutability: Optional

**Image Tagging Strategy:**
```
latest              - Latest build
<commit-hash>       - Git commit hash
v1.0.0              - Semantic version
production          - Production release
```

### 7. CI/CD Pipeline

**CodePipeline Stages:**

```
1. Source Stage
   - Trigger: GitHub webhook
   - Output: Source code artifact

2. Build Stage
   - CodeBuild project
   - Docker image build
   - Push to ECR
   - Output: imagedefinitions.json

3. Deploy Stage
   - ECS service update
   - Rolling deployment
   - Health check validation
```

**CodeBuild Specifications:**
- Compute: BUILD_GENERAL1_SMALL
- Image: aws/codebuild/standard:7.0
- Privileged mode: Enabled (for Docker)
- Cache: S3 bucket

## Security Architecture

### Network Security

```
Internet Gateway
       ↓
   ALB (Public)
       ↓
Security Group (ALB)
  - Inbound: 80, 443 from 0.0.0.0/0
  - Outbound: All
       ↓
Security Group (ECS)
  - Inbound: 3000 from ALB SG
  - Outbound: All
       ↓
Security Group (RDS)
  - Inbound: 3306 from ECS SG
  - Outbound: None
```

### Application Security

1. **Authentication**
   - JWT tokens (1-hour expiration)
   - Refresh tokens (7-day expiration)
   - Bcrypt password hashing (10 rounds)

2. **Authorization**
   - Role-based access control
   - Protected endpoints require JWT
   - Token validation on every request

3. **Input Validation**
   - express-validator middleware
   - SQL injection prevention (parameterized queries)
   - XSS protection (Helmet)

4. **Data Protection**
   - RDS encryption at rest
   - SSL/TLS in transit
   - Secrets in environment variables

### IAM Roles

**ECS Task Execution Role:**
- Pull images from ECR
- Write logs to CloudWatch
- Access Secrets Manager (optional)

**ECS Task Role:**
- Application-specific permissions
- Access to AWS services (if needed)

**CodeBuild Role:**
- Read from S3 (artifacts)
- Push to ECR
- Write logs to CloudWatch

**CodePipeline Role:**
- Trigger CodeBuild
- Update ECS service
- Access S3 artifacts

## Monitoring & Observability

### CloudWatch Metrics

**ECS Metrics:**
- CPUUtilization
- MemoryUtilization
- TaskCount
- TargetResponseTime

**RDS Metrics:**
- CPUUtilization
- DatabaseConnections
- FreeStorageSpace
- ReadLatency / WriteLatency

**ALB Metrics:**
- RequestCount
- TargetResponseTime
- HTTPCode_Target_2XX_Count
- UnHealthyHostCount

### CloudWatch Logs

**Log Groups:**
- `/ecs/singha-loyalty` - Application logs
- `/aws/rds/instance/singha-loyalty-db/error` - RDS errors
- `/aws/codebuild/singha-loyalty-build` - Build logs

**Log Retention:**
- Development: 3 days
- Production: 7 days
- Compliance: 30+ days

### Alarms

**Critical Alarms:**
- ECS CPU > 80% for 5 minutes
- RDS CPU > 90% for 5 minutes
- ALB 5XX errors > 10 in 5 minutes
- RDS storage < 2GB

**Warning Alarms:**
- ECS memory > 70%
- RDS connections > 80% of max
- ALB response time > 1 second

## Scaling Strategy

### Horizontal Scaling (ECS)

**Auto Scaling Policy:**
```yaml
Target Tracking:
  - Metric: CPUUtilization
  - Target: 70%
  - Scale out: Add 1 task
  - Scale in: Remove 1 task
  - Cooldown: 300 seconds

Limits:
  - Min tasks: 2
  - Max tasks: 10
```

### Vertical Scaling (RDS)

**Instance Classes:**
- Development: db.t3.micro (1 vCPU, 1GB)
- Staging: db.t3.small (2 vCPU, 2GB)
- Production: db.t3.medium (2 vCPU, 4GB)

**Storage Scaling:**
- Auto-scaling enabled
- Threshold: 90% full
- Max storage: 100GB

## Disaster Recovery

### Backup Strategy

**RDS Automated Backups:**
- Frequency: Daily
- Retention: 7 days
- Window: 03:00-04:00 UTC

**Manual Snapshots:**
- Before major deployments
- Monthly archival
- Retention: 90 days

### Recovery Procedures

**RTO (Recovery Time Objective):** 1 hour
**RPO (Recovery Point Objective):** 24 hours

**Disaster Scenarios:**

1. **ECS Task Failure**
   - Auto-recovery: ECS restarts task
   - Time: < 2 minutes

2. **AZ Failure**
   - Multi-AZ deployment handles failover
   - Time: < 5 minutes

3. **Region Failure**
   - Manual failover to backup region
   - Restore RDS from snapshot
   - Time: 30-60 minutes

4. **Data Corruption**
   - Restore RDS from point-in-time backup
   - Time: 15-30 minutes

## Cost Optimization

### Current Monthly Costs

| Service | Configuration | Cost |
|---------|--------------|------|
| ECS Fargate Spot | 2 × 0.25 vCPU × 0.5GB | $5-8 |
| RDS MySQL | db.t3.micro, 20GB | $15-20 |
| ALB | 1 load balancer | $16 |
| ECR | Image storage | $1-2 |
| CodePipeline | 1 pipeline | $1 |
| CodeBuild | Build minutes | $2-5 |
| Data Transfer | Moderate | $5-10 |
| **Total** | | **$45-62** |

### Optimization Strategies

1. **Use Fargate Spot** (70% savings)
2. **Right-size RDS instance** (monitor metrics)
3. **Enable RDS auto-pause** (dev environments)
4. **Use CloudFront** (reduce ALB traffic)
5. **Optimize Docker images** (faster deployments)
6. **Set log retention** (reduce storage costs)
7. **Use Reserved Instances** (long-term commitment)

## Performance Optimization

### Application Level

- Connection pooling (10 connections)
- Response compression (gzip)
- Efficient database queries
- Indexed columns
- Caching strategy (Redis optional)

### Infrastructure Level

- Multi-AZ deployment
- Auto-scaling policies
- CloudFront CDN
- ALB connection draining
- ECS task placement strategy

## Future Enhancements

1. **Redis Cache** - Reduce database load
2. **CloudFront** - CDN for static assets
3. **WAF** - Web application firewall
4. **Route 53** - Custom domain + health checks
5. **ElastiCache** - Session management
6. **SQS** - Asynchronous processing
7. **SNS** - Notifications
8. **X-Ray** - Distributed tracing
9. **Secrets Manager** - Credential rotation
10. **Multi-region** - Global deployment

## Conclusion

This architecture provides:
- ✅ Cost-effective deployment ($45-62/month)
- ✅ High availability (Multi-AZ)
- ✅ Auto-scaling capabilities
- ✅ Automated CI/CD pipeline
- ✅ Security best practices
- ✅ Monitoring and observability
- ✅ Disaster recovery procedures
- ✅ Production-ready infrastructure
