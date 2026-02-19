# Visual Guide - AWS Services Connection

## 🎯 Quick Reference: How Everything Connects

This visual guide helps you understand the relationships between AWS services.

---

## 1️⃣ Network Layer (VPC)

```
┌─────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                │
│                                                      │
│  ┌────────────────────┐  ┌────────────────────┐   │
│  │  Public Subnet 1   │  │  Public Subnet 2   │   │
│  │   (10.0.1.0/24)    │  │   (10.0.2.0/24)    │   │
│  │   us-east-1a       │  │   us-east-1b       │   │
│  │                    │  │                    │   │
│  │  ┌──────────┐      │  │  ┌──────────┐      │   │
│  │  │   ALB    │      │  │  │   ALB    │      │   │
│  │  └──────────┘      │  │  └──────────┘      │   │
│  │  ┌──────────┐      │  │  ┌──────────┐      │   │
│  │  │ ECS Task │      │  │  │ ECS Task │      │   │
│  │  └──────────┘      │  │  └──────────┘      │   │
│  └────────────────────┘  └────────────────────┘   │
│                                                      │
│  ┌────────────────────┐  ┌────────────────────┐   │
│  │ Private Subnet 1   │  │ Private Subnet 2   │   │
│  │  (10.0.11.0/24)    │  │  (10.0.12.0/24)    │   │
│  │   us-east-1a       │  │   us-east-1b       │   │
│  │                    │  │                    │   │
│  │  ┌──────────┐      │  │  ┌──────────┐      │   │
│  │  │   RDS    │      │  │  │   RDS    │      │   │
│  │  │ Primary  │      │  │  │ Standby  │      │   │
│  │  └──────────┘      │  │  └──────────┘      │   │
│  └────────────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Key Points:**
- Public subnets have internet access (via Internet Gateway)
- Private subnets are isolated (no direct internet)
- Multi-AZ deployment for high availability

---

## 2️⃣ Security Layer (Security Groups)

```
Internet (0.0.0.0/0)
    │
    │ Port 80/443
    ▼
┌─────────────────┐
│  ALB-SG         │  Allows: HTTP/HTTPS from anywhere
│  (singha-alb-sg)│
└────────┬────────┘
         │ Port 3000
         ▼
┌─────────────────┐
│  ECS-SG         │  Allows: Port 3000 from ALB-SG only
│  (singha-ecs-sg)│
└────────┬────────┘
         │ Port 3306
         ▼
┌─────────────────┐
│  RDS-SG         │  Allows: MySQL from ECS-SG only
│  (singha-rds-sg)│
└─────────────────┘
```

**Key Points:**
- Each layer only accepts traffic from previous layer
- Defense in depth security model
- RDS has no internet access

---

## 3️⃣ Application Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ HTTP Request
     ▼
┌──────────────────────────────────────┐
│  Application Load Balancer (ALB)    │
│  - DNS: xxx.elb.amazonaws.com       │
│  - Listener: Port 80                │
│  - Health Check: /health            │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│  Target Group                        │
│  - Port: 3000                        │
│  - Protocol: HTTP                    │
│  - Health Check: /health every 30s   │
└────┬─────────────────────────────────┘
     │
     ├─────────────┬─────────────┐
     ▼             ▼             ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Task 1  │   │ Task 2  │   │ Task N  │
│ HEALTHY │   │ HEALTHY │   │ HEALTHY │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     └─────────────┴─────────────┘
                   │
                   ▼
          ┌────────────────┐
          │  RDS MySQL     │
          │  Port 3306     │
          └────────────────┘
```

**Key Points:**
- ALB distributes traffic across healthy tasks
- Health checks ensure only healthy tasks receive traffic
- All tasks share same RDS database

---

## 4️⃣ Container Lifecycle

```
┌──────────────────────────────────────────────────┐
│  ECR (Elastic Container Registry)               │
│  Repository: singha-loyalty                      │
│  Image: latest                                   │
└────────────────┬─────────────────────────────────┘
                 │
                 │ Pull Image
                 ▼
┌──────────────────────────────────────────────────┐
│  ECS Cluster: singha-loyalty-cluster            │
│                                                   │
│  ┌────────────────────────────────────────────┐ │
│  │  Service: singha-loyalty-service           │ │
│  │  - Desired Count: 2                        │ │
│  │  - Launch Type: Fargate                    │ │
│  │                                             │ │
│  │  ┌──────────────────────────────────────┐ │ │
│  │  │  Task Definition                      │ │ │
│  │  │  - CPU: 0.25 vCPU                     │ │ │
│  │  │  - Memory: 512 MB                     │ │ │
│  │  │  - Image: ECR URI                     │ │ │
│  │  │  - Port: 3000                         │ │ │
│  │  │  - Env Vars: DB_HOST, JWT_SECRET...  │ │ │
│  │  └──────────────────────────────────────┘ │ │
│  │                                             │ │
│  │  Running Tasks:                             │ │
│  │  ┌─────────┐  ┌─────────┐                 │ │
│  │  │ Task 1  │  │ Task 2  │                 │ │
│  │  │ RUNNING │  │ RUNNING │                 │ │
│  │  └─────────┘  └─────────┘                 │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

**Key Points:**
- Task Definition is the blueprint
- Service maintains desired number of tasks
- Tasks are ephemeral (can be replaced anytime)

---

## 5️⃣ CI/CD Pipeline Flow

```
┌──────────────┐
│   Developer  │
│   git push   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  GitHub Repository                   │
│  Branch: main                        │
└──────┬───────────────────────────────┘
       │ Webhook Trigger
       ▼
┌──────────────────────────────────────┐
│  CodePipeline                        │
│  ┌────────────────────────────────┐ │
│  │  Stage 1: Source               │ │
│  │  - Pull from GitHub            │ │
│  └────────┬───────────────────────┘ │
│           │                          │
│  ┌────────▼───────────────────────┐ │
│  │  Stage 2: Build                │ │
│  │  - CodeBuild Project           │ │
│  │  - docker build                │ │
│  │  - docker push to ECR          │ │
│  └────────┬───────────────────────┘ │
│           │                          │
│  ┌────────▼───────────────────────┐ │
│  │  Stage 3: Deploy               │ │
│  │  - Update ECS Service          │ │
│  │  - Rolling Deployment          │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  ECS Service Updated                 │
│  - New tasks with new image          │
│  - Old tasks drained and stopped     │
└──────────────────────────────────────┘
```

**Key Points:**
- Fully automated from git push to deployment
- Zero-downtime rolling deployment
- Old tasks remain until new tasks are healthy

---

## 6️⃣ Monitoring & Logging

```
┌──────────────────────────────────────────────────┐
│  CloudWatch                                      │
│                                                   │
│  ┌────────────────────────────────────────────┐ │
│  │  Logs                                      │ │
│  │  ┌──────────────────────────────────────┐ │ │
│  │  │  /ecs/singha-loyalty                 │ │ │
│  │  │  - Application logs                  │ │ │
│  │  │  - Error logs                        │ │ │
│  │  │  - Access logs                       │ │ │
│  │  └──────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────┘ │
│                                                   │
│  ┌────────────────────────────────────────────┐ │
│  │  Metrics                                   │ │
│  │  - ECS: CPU, Memory, Task Count           │ │
│  │  - ALB: Request Count, Response Time      │ │
│  │  - RDS: CPU, Connections, Storage         │ │
│  └────────────────────────────────────────────┘ │
│                                                   │
│  ┌────────────────────────────────────────────┐ │
│  │  Alarms                                    │ │
│  │  - High CPU → SNS → Email                 │ │
│  │  - 5XX Errors → SNS → Email               │ │
│  │  - Unhealthy Targets → SNS → Email        │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

**Key Points:**
- All logs centralized in CloudWatch
- Metrics collected automatically
- Alarms notify you of issues

---

## 7️⃣ Request Journey (Detailed)

```
1. User Browser
   │ POST /api/customers/register
   │ Body: {nicNumber, fullName, phoneNumber}
   ▼
2. DNS Resolution
   │ singha-loyalty-alb-xxx.elb.amazonaws.com
   │ → ALB IP Address
   ▼
3. Internet Gateway
   │ Routes to VPC
   ▼
4. Application Load Balancer
   │ - Receives on port 80
   │ - Checks listener rules
   │ - Selects target group
   ▼
5. Target Group
   │ - Checks healthy targets
   │ - Selects Task 1 (round-robin)
   │ - Forwards to port 3000
   ▼
6. ECS Task (Container)
   │ Express.js receives request
   │ ├─ CORS middleware
   │ ├─ Body parser
   │ ├─ Validation middleware
   │ └─ Route handler
   ▼
7. Controller
   │ - Validates NIC format
   │ - Validates phone format
   │ - Checks business rules
   ▼
8. Database Layer
   │ - Gets connection from pool
   │ - Checks for duplicate NIC
   │ - Generates loyalty number
   │ - Inserts customer record
   ▼
9. RDS MySQL
   │ - Executes query
   │ - Returns result
   ▼
10. Response Journey (Reverse)
    │ Controller → Express → Task → Target Group
    │ → ALB → Internet Gateway → User
    ▼
11. User Browser
    │ Receives: {success: true, loyaltyNumber: "1234"}
```

---

## 8️⃣ Scaling Behavior

```
Normal Load:
┌─────┐     ┌─────────┐     ┌─────────┐
│ ALB │────▶│ Task 1  │     │ Task 2  │
└─────┘     │ CPU 30% │     │ CPU 30% │
            └─────────┘     └─────────┘

High Load Detected (CPU > 70%):
┌─────┐     ┌─────────┐     ┌─────────┐
│ ALB │────▶│ Task 1  │     │ Task 2  │
└─────┘     │ CPU 75% │     │ CPU 75% │
            └─────────┘     └─────────┘
                    │
                    │ Auto-Scaling Triggered
                    ▼
            ┌─────────────────┐
            │ New Task 3      │
            │ Starting...     │
            └─────────────────┘

After Scale-Out:
┌─────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ ALB │────▶│ Task 1  │     │ Task 2  │     │ Task 3  │
└─────┘     │ CPU 40% │     │ CPU 40% │     │ CPU 40% │
            └─────────┘     └─────────┘     └─────────┘
```

**Key Points:**
- Auto-scaling based on CPU/Memory metrics
- New tasks added when threshold exceeded
- Tasks removed when load decreases

---

## 9️⃣ Failure Scenarios & Recovery

### Scenario 1: Task Failure
```
Before:
ALB → Task 1 (HEALTHY) ✓
    → Task 2 (HEALTHY) ✓

Task 1 Crashes:
ALB → Task 1 (UNHEALTHY) ✗
    → Task 2 (HEALTHY) ✓

ECS Detects & Replaces:
ALB → Task 1 (STOPPING) ⏸
    → Task 2 (HEALTHY) ✓
    → Task 3 (STARTING) ⏳

After Recovery:
ALB → Task 2 (HEALTHY) ✓
    → Task 3 (HEALTHY) ✓
```

### Scenario 2: AZ Failure
```
Before:
us-east-1a: Task 1 ✓
us-east-1b: Task 2 ✓

AZ-1a Fails:
us-east-1a: Task 1 ✗ (AZ down)
us-east-1b: Task 2 ✓

ECS Replaces in AZ-1b:
us-east-1a: (unavailable)
us-east-1b: Task 2 ✓
           Task 3 ✓ (new)
```

---

## 🔟 Cost Breakdown

```
Monthly AWS Bill: $45-62

┌─────────────────────────────────────┐
│  ECS Fargate Spot                   │
│  2 tasks × 0.25 vCPU × 0.5GB       │
│  $5-8/month                         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  RDS MySQL                          │
│  db.t3.micro + 20GB storage         │
│  $15-20/month                       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Application Load Balancer          │
│  1 ALB + data processing            │
│  $16/month                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Other Services                     │
│  ECR, CodePipeline, CloudWatch      │
│  $10-18/month                       │
└─────────────────────────────────────┘
```

---

## 📚 Service Relationships Summary

| Service | Connects To | Purpose |
|---------|-------------|---------|
| **VPC** | All resources | Network isolation |
| **Internet Gateway** | VPC, ALB | Internet access |
| **ALB** | Target Group | Load distribution |
| **Target Group** | ECS Tasks | Health checks & routing |
| **ECS Cluster** | ECS Service | Logical grouping |
| **ECS Service** | Task Definition | Maintains tasks |
| **Task Definition** | ECR, IAM | Container blueprint |
| **ECS Tasks** | RDS, CloudWatch | Running containers |
| **ECR** | ECS | Image storage |
| **RDS** | ECS Tasks | Data persistence |
| **Security Groups** | All compute | Firewall rules |
| **IAM Roles** | ECS, CodeBuild | Permissions |
| **CloudWatch** | All services | Monitoring & logs |
| **CodePipeline** | GitHub, CodeBuild, ECS | CI/CD orchestration |
| **CodeBuild** | GitHub, ECR | Build & push images |

---

## 🎯 Quick Reference: Where to Find Things

### In AWS Console

**VPC Resources:**
- VPC Dashboard → VPCs, Subnets, Route Tables, Internet Gateways, Security Groups

**Compute:**
- ECS → Clusters, Services, Tasks, Task Definitions
- EC2 → Load Balancers, Target Groups

**Database:**
- RDS → Databases, Subnet Groups

**Container Registry:**
- ECR → Repositories

**CI/CD:**
- CodePipeline → Pipelines
- CodeBuild → Build Projects

**Monitoring:**
- CloudWatch → Logs, Metrics, Alarms, Dashboards

**Security:**
- IAM → Roles, Policies

---

This visual guide should help you understand how all the pieces fit together!
