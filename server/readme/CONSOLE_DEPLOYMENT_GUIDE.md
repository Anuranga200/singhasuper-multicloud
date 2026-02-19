# AWS Console Deployment Guide - Step by Step

## 🎯 Overview

This guide walks you through deploying the Singha Loyalty System using the **AWS Console** (web interface) instead of scripts. This helps you understand how each service connects.

**Estimated Time:** 2-3 hours
**Cost:** $45-62/month

---

## 📋 Prerequisites

Before starting, ensure you have:
- [ ] AWS Account with admin access
- [ ] Docker installed locally
- [ ] Node.js 18+ installed
- [ ] MySQL client installed
- [ ] Text editor for configuration

---

## 🗺️ Deployment Roadmap

```
Phase 1: Networking (VPC, Subnets, Security Groups)
   ↓
Phase 2: Database (RDS MySQL)
   ↓
Phase 3: Container Registry (ECR)
   ↓
Phase 4: Container Orchestration (ECS Cluster)
   ↓
Phase 5: Load Balancer (ALB)
   ↓
Phase 6: Deploy Application (ECS Service)
   ↓
Phase 7: CI/CD Pipeline (CodePipeline)
```

Let's begin!

---


## Phase 1: Networking Setup (30 minutes)

### Step 1.1: Create VPC

**Why:** Virtual Private Cloud isolates your resources

1. Go to **AWS Console** → Search "VPC" → Click **VPC**
2. Click **Create VPC**
3. Configure:
   ```
   Name tag: singha-loyalty-vpc
   IPv4 CIDR block: 10.0.0.0/16
   IPv6 CIDR block: No IPv6 CIDR block
   Tenancy: Default
   ```
4. Click **Create VPC**
5. **Note down VPC ID** (e.g., vpc-xxxxx)

**What you created:** A private network for your resources

---

### Step 1.2: Create Internet Gateway

**Why:** Allows your VPC to communicate with the internet

1. In VPC Dashboard → Click **Internet Gateways** (left menu)
2. Click **Create internet gateway**
3. Configure:
   ```
   Name tag: singha-loyalty-igw
   ```
4. Click **Create internet gateway**
5. Select the gateway → Click **Actions** → **Attach to VPC**
6. Select your VPC (singha-loyalty-vpc)
7. Click **Attach internet gateway**

**Connection:** IGW ↔ VPC

---

### Step 1.3: Create Subnets

**Why:** Subnets divide your VPC into public (internet-facing) and private (internal) sections

#### Public Subnet 1 (for ALB & ECS)

1. Click **Subnets** (left menu) → **Create subnet**
2. Configure:
   ```
   VPC ID: Select singha-loyalty-vpc
   Subnet name: singha-public-subnet-1
   Availability Zone: us-east-1a
   IPv4 CIDR block: 10.0.1.0/24
   ```
3. Click **Create subnet**

#### Public Subnet 2 (for high availability)

1. Click **Create subnet** again
2. Configure:
   ```
   VPC ID: Select singha-loyalty-vpc
   Subnet name: singha-public-subnet-2
   Availability Zone: us-east-1b
   IPv4 CIDR block: 10.0.2.0/24
   ```
3. Click **Create subnet**

#### Private Subnet 1 (for RDS)

1. Click **Create subnet**
2. Configure:
   ```
   VPC ID: Select singha-loyalty-vpc
   Subnet name: singha-private-subnet-1
   Availability Zone: us-east-1a
   IPv4 CIDR block: 10.0.11.0/24
   ```
3. Click **Create subnet**

#### Private Subnet 2 (for RDS high availability)

1. Click **Create subnet**
2. Configure:
   ```
   VPC ID: Select singha-loyalty-vpc
   Subnet name: singha-private-subnet-2
   Availability Zone: us-east-1b
   IPv4 CIDR block: 10.0.12.0/24
   ```
3. Click **Create subnet**

**What you created:** 
- 2 public subnets (for ALB and ECS tasks)
- 2 private subnets (for RDS database)

---

### Step 1.4: Create Route Table for Public Subnets

**Why:** Routes internet traffic through the Internet Gateway

1. Click **Route Tables** (left menu)
2. Find the route table associated with your VPC
3. Click **Create route table**
4. Configure:
   ```
   Name: singha-public-rt
   VPC: singha-loyalty-vpc
   ```
5. Click **Create route table**

#### Add Internet Route

1. Select the route table → Click **Routes** tab
2. Click **Edit routes** → **Add route**
3. Configure:
   ```
   Destination: 0.0.0.0/0
   Target: Internet Gateway → Select singha-loyalty-igw
   ```
4. Click **Save changes**

#### Associate Public Subnets

1. Click **Subnet associations** tab
2. Click **Edit subnet associations**
3. Select:
   - singha-public-subnet-1
   - singha-public-subnet-2
4. Click **Save associations**

**Connection:** Public Subnets → Route Table → Internet Gateway → Internet

---


### Step 1.5: Create Security Groups

**Why:** Security groups act as virtual firewalls

#### Security Group 1: ALB Security Group

1. Click **Security Groups** (left menu) → **Create security group**
2. Configure:
   ```
   Security group name: singha-alb-sg
   Description: Security group for Application Load Balancer
   VPC: singha-loyalty-vpc
   ```

3. **Inbound rules** → Click **Add rule**:
   ```
   Rule 1:
   Type: HTTP
   Protocol: TCP
   Port range: 80
   Source: 0.0.0.0/0 (Anywhere IPv4)
   Description: Allow HTTP from internet
   
   Rule 2:
   Type: HTTPS
   Protocol: TCP
   Port range: 443
   Source: 0.0.0.0/0 (Anywhere IPv4)
   Description: Allow HTTPS from internet
   ```

4. **Outbound rules**: Leave default (All traffic)
5. Click **Create security group**
6. **Note down Security Group ID** (sg-xxxxx)

#### Security Group 2: ECS Security Group

1. Click **Create security group**
2. Configure:
   ```
   Security group name: singha-ecs-sg
   Description: Security group for ECS tasks
   VPC: singha-loyalty-vpc
   ```

3. **Inbound rules** → Click **Add rule**:
   ```
   Type: Custom TCP
   Protocol: TCP
   Port range: 3000
   Source: Custom → Select singha-alb-sg (the ALB security group)
   Description: Allow traffic from ALB
   ```

4. **Outbound rules**: Leave default (All traffic)
5. Click **Create security group**
6. **Note down Security Group ID**

#### Security Group 3: RDS Security Group

1. Click **Create security group**
2. Configure:
   ```
   Security group name: singha-rds-sg
   Description: Security group for RDS MySQL
   VPC: singha-loyalty-vpc
   ```

3. **Inbound rules** → Click **Add rule**:
   ```
   Type: MySQL/Aurora
   Protocol: TCP
   Port range: 3306
   Source: Custom → Select singha-ecs-sg (the ECS security group)
   Description: Allow MySQL from ECS tasks
   ```

4. **Outbound rules**: Leave default
5. Click **Create security group**

**Connection Flow:**
```
Internet → ALB (sg-alb) → ECS Tasks (sg-ecs) → RDS (sg-rds)
```

---

## Phase 2: Database Setup (20 minutes)

### Step 2.1: Create DB Subnet Group

**Why:** Tells RDS which subnets to use

1. Go to **AWS Console** → Search "RDS" → Click **RDS**
2. Click **Subnet groups** (left menu) → **Create DB subnet group**
3. Configure:
   ```
   Name: singha-db-subnet-group
   Description: Subnet group for Singha Loyalty RDS
   VPC: singha-loyalty-vpc
   ```

4. **Add subnets**:
   - Availability Zones: us-east-1a, us-east-1b
   - Subnets: Select singha-private-subnet-1 and singha-private-subnet-2
5. Click **Create**

---

### Step 2.2: Create RDS MySQL Database

**Why:** Your application's data storage

1. Click **Databases** (left menu) → **Create database**
2. **Choose a database creation method**: Standard create
3. **Engine options**:
   ```
   Engine type: MySQL
   Version: MySQL 8.0.43 (or latest)
   ```

4. **Templates**: Free tier (or Dev/Test for production)

5. **Settings**:
   ```
   DB instance identifier: singha-loyalty-db
   Master username: admin
   Master password: [Create strong password - save it!]
   Confirm password: [Same password]
   ```
   **⚠️ IMPORTANT: Save this password securely!**

6. **Instance configuration**:
   ```
   DB instance class: Burstable classes → db.t3.micro
   ```

7. **Storage**:
   ```
   Storage type: General Purpose SSD (gp3)
   Allocated storage: 20 GiB
   Storage autoscaling: Enable (optional)
   Maximum storage threshold: 100 GiB
   ```

8. **Connectivity**:
   ```
   Virtual private cloud (VPC): singha-loyalty-vpc
   DB subnet group: singha-db-subnet-group
   Public access: No
   VPC security group: Choose existing → singha-rds-sg
   Availability Zone: No preference
   ```

9. **Database authentication**: Password authentication

10. **Additional configuration** (expand):
    ```
    Initial database name: singha_loyalty
    DB parameter group: default
    Backup retention period: 7 days
    Backup window: 03:00-04:00 UTC
    Enable encryption: Yes
    ```

11. Click **Create database**

**Wait time:** 10-15 minutes for database to become available

12. Once available, click on the database → **Connectivity & security** tab
13. **Note down the Endpoint** (e.g., singha-loyalty-db.xxxxx.us-east-1.rds.amazonaws.com)

**What you created:** MySQL database in private subnet, accessible only from ECS tasks

---


## Phase 3: Container Registry (15 minutes)

### Step 3.1: Create ECR Repository

**Why:** Stores your Docker images

1. Go to **AWS Console** → Search "ECR" → Click **Elastic Container Registry**
2. Click **Get Started** or **Create repository**
3. Configure:
   ```
   Visibility settings: Private
   Repository name: singha-loyalty
   Tag immutability: Disabled
   Scan on push: Enabled
   KMS encryption: Disabled (use AES-256)
   ```
4. Click **Create repository**
5. **Note down the URI** (e.g., 123456789.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty)

---

### Step 3.2: Build and Push Docker Image

**Why:** Your application needs to be containerized

#### On Your Local Machine:

1. **Navigate to server directory**:
   ```bash
   cd server
   ```

2. **Get your AWS Account ID**:
   ```bash
   aws sts get-caller-identity --query Account --output text
   ```
   Note this down (e.g., 123456789012)

3. **Set variables** (replace with your values):
   ```bash
   export AWS_ACCOUNT_ID=285229572166
   export AWS_REGION=us-east-1
   export ECR_REPO=singha-loyalty
   ```

4. **Login to ECR**:
   ```bash
   aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 285229572166.dkr.ecr.us-east-1.amazonaws.com
   ```
   You should see: "Login Succeeded"

5. **Build Docker image**:
   ```bash
   docker build -t $ECR_REPO:latest .
   docker build -t singha-loyalty:latest .
   ```
   Wait for build to complete (~2-3 minutes)

6. **Tag the image**:
   ```bash
   docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
   docker tag singha-loyalty:latest 285229572166.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest
   ```

7. **Push to ECR**:
   ```bash
   docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
   docker push 285229572166.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest
   ```
   Wait for upload to complete (~2-5 minutes)

8. **Verify in Console**:
   - Go back to ECR in AWS Console
   - Click on your repository
   - You should see an image with tag "latest"

**What you created:** Docker image stored in AWS, ready to be deployed

---

## Phase 4: ECS Cluster Setup (10 minutes)

### Step 4.1: Create ECS Cluster

**Why:** Cluster manages your containers

1. Go to **AWS Console** → Search "ECS" → Click **Elastic Container Service**
2. Click **Clusters** (left menu) → **Create cluster**
3. Configure:
   ```
   Cluster name: singha-loyalty-cluster
   
   Infrastructure:
   ☑ AWS Fargate (serverless)
   
   Monitoring:
   ☑ Use Container Insights
   ```
4. Click **Create**

**What you created:** A cluster that will run your containers

---

### Step 4.2: Create IAM Roles

**Why:** ECS needs permissions to pull images and write logs

#### Task Execution Role

1. Go to **AWS Console** → Search "IAM" → Click **IAM**
2. Click **Roles** (left menu) → **Create role**
3. **Trusted entity type**: AWS service
4. **Use case**: Elastic Container Service → Elastic Container Service Task
5. Click **Next**
6. **Add permissions**: Search and select:
   - `AmazonECSTaskExecutionRolePolicy`
7. Click **Next**
8. **Role name**: `singha-ecs-task-execution-role`
9. Click **Create role**

#### Task Role

1. Click **Create role** again
2. **Trusted entity type**: AWS service
3. **Use case**: Elastic Container Service → Elastic Container Service Task
4. Click **Next**
5. **Add permissions**: (None needed for now, can add later)
6. Click **Next**
7. **Role name**: `singha-ecs-task-role`
8. Click **Create role**

**What you created:** Permissions for ECS to run your containers

---


## Phase 5: Load Balancer Setup (20 minutes)

### Step 5.1: Create Target Group

**Why:** Target group routes traffic to your ECS tasks

1. Go to **AWS Console** → Search "EC2" → Click **EC2**
2. Scroll down → Click **Target Groups** (left menu under Load Balancing)
3. Click **Create target group**
4. Configure:
   ```
   Choose a target type: IP addresses
   Target group name: singha-loyalty-tg
   Protocol: HTTP
   Port: 3000
   VPC: singha-loyalty-vpc
   Protocol version: HTTP1
   ```

5. **Health checks**:
   ```
   Health check protocol: HTTP
   Health check path: /health
   Advanced health check settings:
     - Healthy threshold: 2
     - Unhealthy threshold: 3
     - Timeout: 5 seconds
     - Interval: 30 seconds
     - Success codes: 200
   ```

6. Click **Next**
7. **Register targets**: Skip this (ECS will register automatically)
8. Click **Create target group**

---

### Step 5.2: Create Application Load Balancer

**Why:** Distributes traffic across your containers

1. Click **Load Balancers** (left menu) → **Create load balancer**
2. Select **Application Load Balancer** → Click **Create**
3. **Basic configuration**:
   ```
   Load balancer name: singha-loyalty-alb
   Scheme: Internet-facing
   IP address type: IPv4
   ```

4. **Network mapping**:
   ```
   VPC: singha-loyalty-vpc
   Mappings: Select 2 availability zones
     ☑ us-east-1a → singha-public-subnet-1
     ☑ us-east-1b → singha-public-subnet-2
   ```

5. **Security groups**:
   - Remove default
   - Select: singha-alb-sg

6. **Listeners and routing**:
   ```
   Protocol: HTTP
   Port: 80
   Default action: Forward to → singha-loyalty-tg
   ```

7. **Summary**: Review settings
8. Click **Create load balancer**

**Wait time:** 2-3 minutes for ALB to become active

9. Once active, click on the load balancer
10. **Note down the DNS name** (e.g., singha-loyalty-alb-xxxxx.us-east-1.elb.amazonaws.com)

**What you created:** Load balancer that will distribute traffic to your containers

**Connection:** Internet → ALB → Target Group → (ECS Tasks will be added next)

---

## Phase 6: Deploy Application (30 minutes)

### Step 6.1: Create CloudWatch Log Group

**Why:** Store application logs

1. Go to **AWS Console** → Search "CloudWatch" → Click **CloudWatch**
2. Click **Log groups** (left menu) → **Create log group**
3. Configure:
   ```
   Log group name: /ecs/singha-loyalty
   Retention setting: 7 days
   ```
4. Click **Create**

---

### Step 6.2: Create Task Definition

**Why:** Defines how your container should run

1. Go back to **ECS** → Click **Task definitions** (left menu)
2. Click **Create new task definition** → **Create new task definition**
3. **Task definition family**: `singha-loyalty-task`

4. **Infrastructure requirements**:
   ```
   Launch type: AWS Fargate
   Operating system/Architecture: Linux/X86_64
   Task size:
     - CPU: 0.25 vCPU
     - Memory: 0.5 GB
   Task role: singha-ecs-task-role
   Task execution role: singha-ecs-task-execution-role
   ```

5. **Container - 1**:
   Click **Add container**
   
   **Container details**:
   ```
   Name: singha-loyalty-container
   Image URI: [Your ECR URI]:latest
   Example: 123456789.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest
   
   Essential container: Yes
   ```

   **Port mappings**:
   ```
   Container port: 3000
   Protocol: TCP
   Port name: singha-3000-tcp
   App protocol: HTTP
   ```

   **Environment variables** - Click **Add environment variable** for each:
   ```
   NODE_ENV = production
   PORT = 3000
   DB_HOST = [Your RDS Endpoint]
   DB_PORT = 3306
   DB_USER = admin
   DB_PASSWORD = [Your DB Password]
   DB_NAME = singha_loyalty
   JWT_SECRET = [Generate random 32-char string]
   JWT_REFRESH_SECRET = [Generate another random 32-char string]
   CORS_ORIGIN = *
   ```

   **⚠️ IMPORTANT**: Replace values with your actual:
   - RDS endpoint (from Phase 2)
   - DB password (from Phase 2)
   - JWT secrets (generate random strings)

   **Logging**:
   ```
   Log driver: awslogs
   awslogs-group: /ecs/singha-loyalty
   awslogs-region: us-east-1
   awslogs-stream-prefix: ecs
   ```

6. Click **Create**

**What you created:** Blueprint for running your container

---


### Step 6.3: Create ECS Service

**Why:** Runs and maintains your containers

1. Go to **ECS** → **Clusters** → Click **singha-loyalty-cluster**
2. Click **Services** tab → **Create**
3. **Environment**:
   ```
   Compute options: Launch type
   Launch type: FARGATE
   Platform version: LATEST
   ```

4. **Deployment configuration**:
   ```
   Application type: Service
   Family: singha-loyalty-task
   Revision: LATEST
   Service name: singha-loyalty-service
   Desired tasks: 2
   ```

5. **Networking**:
   ```
   VPC: singha-loyalty-vpc
   Subnets: Select both public subnets
     - singha-public-subnet-1
     - singha-public-subnet-2
   Security group: Use existing → singha-ecs-sg
   Public IP: ENABLED
   ```

6. **Load balancing**:
   ```
   Load balancer type: Application Load Balancer
   Load balancer: singha-loyalty-alb
   
   Container to load balance:
     - Container: singha-loyalty-container 3000:3000
     - Click "Add"--------------
   
   Listener: Use an existing listener → 80:HTTP
   Target group: Use an existing target group → singha-loyalty-tg
   
   Health check grace period: 60 seconds
   ```

7. **Service auto scaling**: (Optional - skip for now)

8. Click **Create**

**Wait time:** 5-10 minutes for tasks to start

9. **Monitor deployment**:
   - Click on the service
   - Go to **Tasks** tab
   - Wait for tasks to show "RUNNING" status
   - Check **Health status** shows "HEALTHY"

**What you created:** Running application with 2 containers behind load balancer

**Connection Flow:**
```
Internet → ALB → Target Group → ECS Service (2 tasks) → RDS
```

---

### Step 6.4: Test Your Application

1. **Get ALB DNS name** (from Phase 5)
2. **Test health check**:
   ```bash
   curl http://[ALB-DNS-NAME]/health
   ```
   Expected: `{"status":"healthy","timestamp":"...","uptime":...}`

3. **Test customer registration**:
   ```bash
   curl -X POST http://singha-loyalty-alb-467491726.us-east-1.elb.amazonaws.com/api/customers/register \
     -H "Content-Type: application/json" \
     -d '{
       "nicNumber": "123456789V",
       "fullName": "Test User",
       "phoneNumber": "0771234567"
     }'
   ```

4. **If you get errors**, check CloudWatch Logs:
   - Go to CloudWatch → Log groups → /ecs/singha-loyalty
   - Click on latest log stream
   - Look for error messages

---

## Phase 7: Database Initialization (15 minutes)

### Step 7.1: Connect to RDS

**Option A: Using MySQL Workbench (Recommended)**

1. Download MySQL Workbench: https://dev.mysql.com/downloads/workbench/
2. Open MySQL Workbench
3. Click **+** to create new connection
4. Configure:
   ```
   Connection Name: Singha Loyalty DB
   Hostname: [Your RDS Endpoint]
   Port: 3306
   Username: admin
   Password: [Your DB Password]
   Default Schema: singha_loyalty
   ```
5. Click **Test Connection** → Should succeed
6. Click **OK**

**Option B: Using Command Line**

```bash
mysql -h [RDS-ENDPOINT] -u admin -p
# Enter password when prompted
```

---

### Step 7.2: Run Database Migrations

1. **Copy the schema SQL**:
   - Open `server/src/db/schema.sql` from your project
   - Copy all content

2. **In MySQL Workbench**:
   - Connect to your database
   - Click **Query** → New Query Tab
   - Paste the schema SQL
   - Click **Execute** (lightning bolt icon)

3. **Verify tables created**:
   ```sql
   USE singha_loyalty;
   SHOW TABLES;
   ```
   You should see: `admins`, `customers`

---

### Step 7.3: Seed Initial Data

1. **On your local machine**:
   ```bash
   cd server
   npm install
   ```

2. **Update .env file**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```
   DB_HOST=[Your RDS Endpoint]
   DB_PORT=3306
   DB_USER=admin
   DB_PASSWORD=[Your DB Password]
   DB_NAME=singha_loyalty
   ```

3. **Run seed script**:
   ```bash
   npm run seed
   ```

4. **Verify data**:
   ```sql
   SELECT * FROM admins;
   SELECT * FROM customers;
   ```

**What you created:** Database with schema and initial admin user

---


## Phase 8: CI/CD Pipeline (Optional - 45 minutes)

### Step 8.1: Create S3 Bucket for Artifacts

**Why:** Stores build artifacts

1. Go to **AWS Console** → Search "S3" → Click **S3**
2. Click **Create bucket**
3. Configure:
   ```
   Bucket name: singha-loyalty-pipeline-artifacts-[YOUR-ACCOUNT-ID]
   AWS Region: us-east-1
   Block all public access: ☑ (keep checked)
   Bucket Versioning: Enable
   ```
4. Click **Create bucket**

---

### Step 8.2: Create CodeBuild IAM Role

1. Go to **IAM** → **Roles** → **Create role**
2. **Trusted entity**: AWS service
3. **Use case**: CodeBuild
4. Click **Next**
5. **Add permissions**: Search and attach:
   - `AmazonEC2ContainerRegistryPowerUser`
   - `CloudWatchLogsFullAccess`
6. Click **Next**
7. **Role name**: `singha-codebuild-role`
8. Click **Create role**

9. **Add inline policy for S3**:
   - Click on the role
   - Click **Add permissions** → **Create inline policy**
   - Click **JSON** tab
   - Paste:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject"
         ],
         "Resource": "arn:aws:s3:::singha-loyalty-pipeline-artifacts-*/*"
       }
     ]
   }
   ```
   - Click **Review policy**
   - Name: `S3ArtifactAccess`
   - Click **Create policy**

---

### Step 8.3: Create CodeBuild Project

**Why:** Builds your Docker image automatically

1. Go to **AWS Console** → Search "CodeBuild" → Click **CodeBuild**
2. Click **Create build project**
3. **Project configuration**:
   ```
   Project name: singha-loyalty-build
   Description: Build Docker image for Singha Loyalty
   ```

4. **Source**:
   ```
   Source provider: GitHub
   Repository: Connect using OAuth (click "Connect to GitHub")
   GitHub repository: [Your repository URL]
   Source version: main (or your branch)
   ```

5. **Environment**:
   ```
   Environment image: Managed image
   Operating system: Amazon Linux 2
   Runtime: Standard
   Image: aws/codebuild/standard:7.0
   Image version: Always use the latest
   Environment type: Linux
   Privileged: ☑ (Enable - required for Docker)
   Service role: Existing service role → singha-codebuild-role
   ```

6. **Buildspec**:
   ```
   Build specifications: Use a buildspec file
   Buildspec name: infrastructure/buildspec.yml
   ```

7. **Artifacts**:
   ```
   Type: Amazon S3
   Bucket name: singha-loyalty-pipeline-artifacts-[YOUR-ACCOUNT-ID]
   Name: BuildArtifact
   Artifacts packaging: None
   ```

8. **Logs**:
   ```
   CloudWatch logs: Enabled
   Group name: /aws/codebuild/singha-loyalty-build
   ```

9. Click **Create build project**

---

### Step 8.4: Create CodePipeline IAM Role

1. Go to **IAM** → **Roles** → **Create role**
2. **Trusted entity**: AWS service
3. **Use case**: CodePipeline
4. Click **Next**
5. Policies are auto-attached
6. Click **Next**
7. **Role name**: `singha-codepipeline-role`
8. Click **Create role**

9. **Add inline policy for ECS**:
   - Click on the role
   - Click **Add permissions** → **Create inline policy**
   - Click **JSON** tab
   - Paste:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ecs:*",
           "iam:PassRole"
         ],
         "Resource": "*"
       }
     ]
   }
   ```
   - Name: `ECSDeployAccess`
   - Click **Create policy**

---

### Step 8.5: Create CodePipeline

**Why:** Automates deployment on code changes

1. Go to **AWS Console** → Search "CodePipeline" → Click **CodePipeline**
2. Click **Create pipeline**
3. **Pipeline settings**:
   ```
   Pipeline name: singha-loyalty-pipeline
   Service role: Existing service role → singha-codepipeline-role
   ```
4. Click **Next**

5. **Source stage**:
   ```
   Source provider: GitHub (Version 2)
   Connection: Click "Connect to GitHub"
     - Connection name: github-connection
     - Click "Connect to GitHub"
     - Authorize AWS
   Repository name: [Your repository]
   Branch name: main
   Output artifact format: CodePipeline default
   ```
6. Click **Next**

7. **Build stage**:
   ```
   Build provider: AWS CodeBuild
   Region: US East (N. Virginia)
   Project name: singha-loyalty-build
   Build type: Single build
   ```
8. Click **Next**

9. **Deploy stage**:
   ```
   Deploy provider: Amazon ECS
   Region: US East (N. Virginia)
   Cluster name: singha-loyalty-cluster
   Service name: singha-loyalty-service
   Image definitions file: imagedefinitions.json
   ```
10. Click **Next**

11. **Review** → Click **Create pipeline**

**Pipeline will start automatically!**

---

### Step 8.6: Monitor Pipeline

1. Watch the pipeline execute:
   - **Source**: Pulls code from GitHub
   - **Build**: Builds Docker image, pushes to ECR
   - **Deploy**: Updates ECS service

2. **If build fails**:
   - Click on **Details** in Build stage
   - Check logs for errors
   - Common issues:
     - Buildspec file path wrong
     - Docker build errors
     - ECR permissions

3. **If deploy fails**:
   - Check ECS service events
   - Check task logs in CloudWatch

**What you created:** Automated deployment pipeline

**Flow:**
```
Git Push → GitHub → CodePipeline → CodeBuild → ECR → ECS Service Update
```

---


## Phase 9: Monitoring & Verification (15 minutes)

### Step 9.1: View Application Logs

1. Go to **CloudWatch** → **Log groups**
2. Click `/ecs/singha-loyalty`
3. Click on latest log stream
4. You should see:
   ```
   🚀 Server running on port 3000
   📊 Environment: production
   ✅ Database connected successfully
   ```

---

### Step 9.2: Check ECS Service Health

1. Go to **ECS** → **Clusters** → **singha-loyalty-cluster**
2. Click **singha-loyalty-service**
3. **Verify**:
   - Running tasks: 2
   - Desired tasks: 2
   - Health status: HEALTHY

4. Click **Tasks** tab
5. Click on a task
6. Check:
   - Last status: RUNNING
   - Health status: HEALTHY
   - Container status: RUNNING

---

### Step 9.3: Check Target Group Health

1. Go to **EC2** → **Target Groups**
2. Click **singha-loyalty-tg**
3. Click **Targets** tab
4. Both targets should show:
   - Status: healthy
   - Health status: Healthy

---

### Step 9.4: Test All Endpoints

**1. Health Check**
```bash
curl http://[ALB-DNS]/health
```
Expected: `{"status":"healthy",...}`

**2. Customer Registration**
```bash
curl -X POST http://[ALB-DNS]/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "nicNumber": "999888777V",
    "fullName": "John Doe",
    "phoneNumber": "0771234567"
  }'
```
Expected: `{"success":true,"loyaltyNumber":"XXXX"}`

**3. Admin Login**
```bash
curl -X POST http://[ALB-DNS]/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@singha.com",
    "password": "Admin@123"
  }'
```
Expected: `{"success":true,"token":"eyJ..."}`

**4. Get Customers (Protected)**
```bash
# Save token from login
TOKEN="eyJ..."

curl http://[ALB-DNS]/api/customers \
  -H "Authorization: Bearer $TOKEN"
```
Expected: `{"customers":[...],"count":...}`

---

### Step 9.5: Create CloudWatch Dashboard

**Why:** Visual monitoring of your application

1. Go to **CloudWatch** → **Dashboards**
2. Click **Create dashboard**
3. **Dashboard name**: `singha-loyalty-dashboard`
4. Click **Create dashboard**

5. **Add widgets**:

   **Widget 1: ECS CPU**
   - Click **Add widget** → **Line**
   - **Metrics** → **ECS** → **ClusterName, ServiceName**
   - Select: `CPUUtilization` for your service
   - Click **Create widget**

   **Widget 2: ECS Memory**
   - Click **Add widget** → **Line**
   - Select: `MemoryUtilization` for your service
   - Click **Create widget**

   **Widget 3: ALB Request Count**
   - Click **Add widget** → **Line**
   - **Metrics** → **ApplicationELB** → **Per AppELB Metrics**
   - Select: `RequestCount` for your ALB
   - Click **Create widget**

   **Widget 4: RDS CPU**
   - Click **Add widget** → **Line**
   - **Metrics** → **RDS** → **Per-Database Metrics**
   - Select: `CPUUtilization` for your database
   - Click **Create widget**

6. Click **Save dashboard**

---

### Step 9.6: Set Up Alarms

**Alarm 1: High ECS CPU**

1. Go to **CloudWatch** → **Alarms** → **Create alarm**
2. Click **Select metric**
3. **ECS** → **ClusterName, ServiceName**
4. Select `CPUUtilization` for your service
5. Click **Select metric**
6. Configure:
   ```
   Statistic: Average
   Period: 5 minutes
   Threshold type: Static
   Whenever CPUUtilization is: Greater than 80
   ```
7. Click **Next**
8. **Notification**: Create new SNS topic
   ```
   Topic name: singha-alerts
   Email: your-email@example.com
   ```
9. Click **Create topic**
10. Click **Next**
11. **Alarm name**: `singha-ecs-high-cpu`
12. Click **Next** → **Create alarm**

**Alarm 2: RDS High CPU**

1. Repeat above steps but select RDS CPUUtilization
2. Threshold: Greater than 90
3. Name: `singha-rds-high-cpu`

**Alarm 3: ALB 5XX Errors**

1. Select ALB metric: `HTTPCode_Target_5XX_Count`
2. Threshold: Greater than 10
3. Name: `singha-alb-5xx-errors`

**⚠️ Check your email and confirm SNS subscription!**

---

## Phase 10: Update Frontend (10 minutes)

### Step 10.1: Update Frontend Configuration

1. **In your project root**, edit `.env`:
   ```
   VITE_API_BASE_URL=http://[YOUR-ALB-DNS]/api
   ```

2. **Build frontend**:
   ```bash
   npm run build
   ```

3. **Test locally**:
   ```bash
   npm run preview
   ```
   - Open browser to http://localhost:4173
   - Test registration form
   - Test admin login

---

### Step 10.2: Deploy Frontend to S3 (Optional)

**Create S3 Bucket for Frontend**

1. Go to **S3** → **Create bucket**
2. Configure:
   ```
   Bucket name: singha-loyalty-frontend
   Region: us-east-1
   Block all public access: ☐ (Uncheck)
   ```
3. Click **Create bucket**

**Enable Static Website Hosting**

1. Click on bucket → **Properties** tab
2. Scroll to **Static website hosting**
3. Click **Edit**
4. Configure:
   ```
   Static website hosting: Enable
   Hosting type: Host a static website
   Index document: index.html
   Error document: index.html
   ```
5. Click **Save changes**

**Upload Frontend Files**

1. Click **Objects** tab → **Upload**
2. Click **Add files** → Select all files from `dist/` folder
3. Click **Upload**

**Make Files Public**

1. Select all uploaded files
2. Click **Actions** → **Make public using ACL**
3. Click **Make public**

**Access Your Frontend**

1. Go to **Properties** tab
2. Scroll to **Static website hosting**
3. Copy the **Bucket website endpoint**
4. Open in browser

---


## 🎯 Complete Architecture Visualization

Now that everything is deployed, here's how all services connect:

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Route 53 (Optional)│
              │   Custom Domain      │
              └──────────┬───────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                    AWS REGION: us-east-1                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │              VPC (10.0.0.0/16)                              ││
│  │                                                              ││
│  │  ┌──────────────────────────────────────────────────────┐  ││
│  │  │         PUBLIC SUBNETS (us-east-1a, us-east-1b)      │  ││
│  │  │                                                        │  ││
│  │  │  ┌──────────────────────────────────────────────┐    │  ││
│  │  │  │  Application Load Balancer                   │    │  ││
│  │  │  │  - DNS: xxx.elb.amazonaws.com                │    │  ││
│  │  │  │  - Security Group: singha-alb-sg             │    │  ││
│  │  │  │  - Listener: HTTP:80 → Target Group          │    │  ││
│  │  │  └────────────────┬─────────────────────────────┘    │  ││
│  │  │                   │                                    │  ││
│  │  │                   ▼                                    │  ││
│  │  │  ┌──────────────────────────────────────────────┐    │  ││
│  │  │  │  Target Group: singha-loyalty-tg             │    │  ││
│  │  │  │  - Health Check: /health                     │    │  ││
│  │  │  │  - Port: 3000                                │    │  ││
│  │  │  └────────────────┬─────────────────────────────┘    │  ││
│  │  │                   │                                    │  ││
│  │  │         ┌─────────┴─────────┐                         │  ││
│  │  │         ▼                   ▼                         │  ││
│  │  │  ┌─────────────┐     ┌─────────────┐                 │  ││
│  │  │  │ ECS Task 1  │     │ ECS Task 2  │                 │  ││
│  │  │  │ (Fargate)   │     │ (Fargate)   │                 │  ││
│  │  │  │ - 0.25 vCPU │     │ - 0.25 vCPU │                 │  ││
│  │  │  │ - 512 MB    │     │ - 512 MB    │                 │  ││
│  │  │  │ - Port 3000 │     │ - Port 3000 │                 │  ││
│  │  │  │ - SG: ecs-sg│     │ - SG: ecs-sg│                 │  ││
│  │  │  └──────┬──────┘     └──────┬──────┘                 │  ││
│  │  └─────────┼────────────────────┼────────────────────────┘  ││
│  │            │                    │                            ││
│  │            └────────┬───────────┘                            ││
│  │                     │                                        ││
│  │  ┌──────────────────▼────────────────────────────────────┐  ││
│  │  │      PRIVATE SUBNETS (us-east-1a, us-east-1b)         │  ││
│  │  │                                                         │  ││
│  │  │  ┌───────────────────────────────────────────────┐    │  ││
│  │  │  │  RDS MySQL: singha-loyalty-db                 │    │  ││
│  │  │  │  - Instance: db.t3.micro                      │    │  ││
│  │  │  │  - Storage: 20GB gp3                          │    │  ││
│  │  │  │  - Database: singha_loyalty                   │    │  ││
│  │  │  │  - Security Group: singha-rds-sg              │    │  ││
│  │  │  │  - Port: 3306                                 │    │  ││
│  │  │  └───────────────────────────────────────────────┘    │  ││
│  │  └─────────────────────────────────────────────────────────┘││
│  └────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    CONTAINER REGISTRY                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ECR: singha-loyalty                                     │  │
│  │  - Image: latest                                         │  │
│  │  - Scan on push: Enabled                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                      CI/CD PIPELINE                             │
│                                                                  │
│  GitHub Repository                                              │
│       ↓ (webhook)                                               │
│  CodePipeline: singha-loyalty-pipeline                          │
│       ↓                                                          │
│  CodeBuild: singha-loyalty-build                                │
│       ↓ (docker build & push)                                   │
│  ECR: singha-loyalty:latest                                     │
│       ↓ (update service)                                        │
│  ECS Service: singha-loyalty-service                            │
│       ↓ (rolling deployment)                                    │
│  New Tasks Running                                              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    MONITORING & LOGGING                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CloudWatch Logs                                         │  │
│  │  - /ecs/singha-loyalty (Application logs)               │  │
│  │  - /aws/codebuild/singha-loyalty-build (Build logs)     │  │
│  │  - /aws/rds/instance/singha-loyalty-db (DB logs)        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CloudWatch Alarms                                       │  │
│  │  - singha-ecs-high-cpu                                   │  │
│  │  - singha-rds-high-cpu                                   │  │
│  │  - singha-alb-5xx-errors                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CloudWatch Dashboard                                    │  │
│  │  - singha-loyalty-dashboard                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Flow

```
1. User Request
   ↓
2. Internet Gateway (public access)
   ↓
3. ALB Security Group (allows 80/443 from 0.0.0.0/0)
   ↓
4. Application Load Balancer
   ↓
5. ECS Security Group (allows 3000 from ALB SG only)
   ↓
6. ECS Tasks (in public subnet with public IP)
   ↓
7. RDS Security Group (allows 3306 from ECS SG only)
   ↓
8. RDS MySQL (in private subnet, no public access)
```

---

## 📊 Data Flow Example: Customer Registration

```
1. User submits form on frontend
   ↓
2. POST /api/customers/register → ALB DNS
   ↓
3. ALB receives request on port 80
   ↓
4. ALB forwards to Target Group (port 3000)
   ↓
5. Target Group routes to healthy ECS task
   ↓
6. ECS Task (Express.js) receives request
   ↓
7. Validation middleware checks input
   ↓
8. Controller processes request
   ↓
9. Database connection pool gets connection
   ↓
10. Query sent to RDS MySQL (port 3306)
    ↓
11. RDS checks for duplicate NIC
    ↓
12. RDS inserts new customer record
    ↓
13. Response flows back through chain
    ↓
14. User receives loyalty number
```

---

## 🎓 Understanding Service Connections

### 1. VPC → Subnets
- **VPC** is your private network (10.0.0.0/16)
- **Public subnets** have route to Internet Gateway
- **Private subnets** have no direct internet access
- **Why**: Isolate database from internet

### 2. Security Groups
- **ALB SG**: Allows internet traffic (80/443)
- **ECS SG**: Only allows traffic from ALB
- **RDS SG**: Only allows traffic from ECS
- **Why**: Defense in depth - each layer protected

### 3. Load Balancer → Target Group → ECS
- **ALB**: Entry point, distributes traffic
- **Target Group**: Defines health checks and routing
- **ECS Tasks**: Automatically registered as targets
- **Why**: High availability and health monitoring

### 4. ECS Cluster → Service → Tasks
- **Cluster**: Logical grouping
- **Service**: Maintains desired task count
- **Tasks**: Running containers
- **Why**: Auto-recovery and scaling

### 5. Task Definition → Container
- **Task Definition**: Blueprint (CPU, memory, image)
- **Container**: Running instance of image
- **Environment Variables**: Configuration
- **Why**: Consistent deployments

### 6. ECR → ECS
- **ECR**: Stores Docker images
- **ECS**: Pulls images to run
- **Task Execution Role**: Provides pull permissions
- **Why**: Private, secure image storage

### 7. CodePipeline → CodeBuild → ECS
- **Pipeline**: Orchestrates workflow
- **CodeBuild**: Builds and pushes image
- **ECS**: Deploys new image
- **Why**: Automated deployments

---


## 🧪 Testing & Verification Checklist

### Infrastructure Tests

- [ ] **VPC Created**
  - Go to VPC Dashboard
  - Verify: singha-loyalty-vpc exists
  - CIDR: 10.0.0.0/16

- [ ] **Subnets Created**
  - 2 public subnets in different AZs
  - 2 private subnets in different AZs
  - Public subnets have route to IGW

- [ ] **Security Groups Configured**
  - ALB SG: Allows 80/443 from internet
  - ECS SG: Allows 3000 from ALB SG
  - RDS SG: Allows 3306 from ECS SG

- [ ] **RDS Database Running**
  - Status: Available
  - Endpoint accessible from ECS
  - Database: singha_loyalty exists

- [ ] **ECR Repository Created**
  - Repository: singha-loyalty
  - Image: latest tag exists

- [ ] **ECS Cluster Running**
  - Cluster: singha-loyalty-cluster
  - Service: singha-loyalty-service
  - Tasks: 2 running, 2 healthy

- [ ] **Load Balancer Active**
  - ALB: singha-loyalty-alb
  - State: Active
  - Target Group: 2 healthy targets

### Application Tests

- [ ] **Health Check**
  ```bash
  curl http://[ALB-DNS]/health
  # Expected: {"status":"healthy",...}
  ```

- [ ] **Customer Registration**
  ```bash
  curl -X POST http://[ALB-DNS]/api/customers/register \
    -H "Content-Type: application/json" \
    -d '{"nicNumber":"111222333V","fullName":"Test","phoneNumber":"0771234567"}'
  # Expected: {"success":true,"loyaltyNumber":"XXXX"}
  ```

- [ ] **Duplicate Registration (Should Fail)**
  ```bash
  # Try same NIC again
  # Expected: {"error":"This NIC number is already registered."}
  ```

- [ ] **Admin Login**
  ```bash
  curl -X POST http://[ALB-DNS]/api/admin/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@singha.com","password":"Admin@123"}'
  # Expected: {"success":true,"token":"eyJ..."}
  ```

- [ ] **Get Customers (Protected)**
  ```bash
  TOKEN="[your-token]"
  curl http://[ALB-DNS]/api/customers \
    -H "Authorization: Bearer $TOKEN"
  # Expected: {"customers":[...],"count":...}
  ```

- [ ] **Invalid Token (Should Fail)**
  ```bash
  curl http://[ALB-DNS]/api/customers \
    -H "Authorization: Bearer invalid-token"
  # Expected: 401 Unauthorized
  ```

### Monitoring Tests

- [ ] **CloudWatch Logs**
  - Log group: /ecs/singha-loyalty exists
  - Recent log streams visible
  - Application logs showing

- [ ] **CloudWatch Alarms**
  - 3 alarms created
  - SNS topic configured
  - Email subscription confirmed

- [ ] **CloudWatch Dashboard**
  - Dashboard: singha-loyalty-dashboard
  - 4 widgets showing metrics

### CI/CD Tests (If Configured)

- [ ] **Pipeline Created**
  - Pipeline: singha-loyalty-pipeline
  - 3 stages: Source, Build, Deploy

- [ ] **Manual Trigger**
  - Click "Release change"
  - All stages succeed

- [ ] **Git Push Trigger**
  - Make code change
  - Push to GitHub
  - Pipeline auto-triggers
  - Deployment succeeds

---

## 🐛 Troubleshooting Guide

### Issue: ECS Tasks Not Starting

**Symptoms:**
- Tasks stuck in PENDING
- Tasks start then stop immediately

**Check:**
1. **CloudWatch Logs**:
   ```
   Go to: CloudWatch → Log groups → /ecs/singha-loyalty
   Look for: Error messages in latest stream
   ```

2. **Task Definition**:
   - Verify image URI is correct
   - Check environment variables
   - Verify IAM roles attached

3. **Common Errors**:
   - `CannotPullContainerError`: Check ECR permissions
   - `Database connection failed`: Check RDS endpoint and credentials
   - `Port already in use`: Check port mapping (should be 3000)

**Solution:**
```bash
# Check task stopped reason
aws ecs describe-tasks \
  --cluster singha-loyalty-cluster \
  --tasks [TASK-ARN] \
  --query 'tasks[0].stoppedReason'
```

---

### Issue: ALB Returns 503 Service Unavailable

**Symptoms:**
- curl returns 503 error
- Target group shows unhealthy targets

**Check:**
1. **Target Group Health**:
   ```
   EC2 → Target Groups → singha-loyalty-tg → Targets tab
   Look for: Health status and reason
   ```

2. **Health Check Configuration**:
   - Path: /health
   - Port: 3000
   - Success codes: 200

3. **ECS Task Health**:
   ```
   ECS → Clusters → singha-loyalty-cluster → Tasks
   Check: Health status of tasks
   ```

**Solution:**
- If health check failing: Verify /health endpoint works
- If no targets: Check ECS service is running
- If targets draining: Wait for new tasks to become healthy

---

### Issue: Database Connection Failed

**Symptoms:**
- Application logs show "Database connection failed"
- Tasks keep restarting

**Check:**
1. **RDS Status**:
   ```
   RDS → Databases → singha-loyalty-db
   Status should be: Available
   ```

2. **Security Group**:
   ```
   RDS → singha-loyalty-db → Connectivity & security
   Verify: singha-rds-sg allows 3306 from singha-ecs-sg
   ```

3. **Environment Variables**:
   ```
   ECS → Task Definitions → singha-loyalty-task
   Verify: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
   ```

**Solution:**
```bash
# Test connection from local machine (if RDS is public)
mysql -h [RDS-ENDPOINT] -u admin -p

# Or check from ECS task
aws ecs execute-command \
  --cluster singha-loyalty-cluster \
  --task [TASK-ID] \
  --container singha-loyalty-container \
  --interactive \
  --command "/bin/sh"

# Inside container:
nc -zv [RDS-ENDPOINT] 3306
```

---

### Issue: Pipeline Build Fails

**Symptoms:**
- CodeBuild stage fails
- Red X in pipeline

**Check:**
1. **Build Logs**:
   ```
   CodeBuild → Build projects → singha-loyalty-build
   Click on failed build → View logs
   ```

2. **Common Errors**:
   - `buildspec.yml not found`: Check file path
   - `Docker build failed`: Check Dockerfile syntax
   - `ECR push failed`: Check IAM permissions

**Solution:**
```bash
# Test build locally
cd server
docker build -t test .

# Check buildspec path
ls infrastructure/buildspec.yml
```

---

### Issue: High Costs

**Symptoms:**
- AWS bill higher than expected

**Check:**
1. **Cost Explorer**:
   ```
   AWS Console → Cost Explorer
   Group by: Service
   Time range: Last 7 days
   ```

2. **Common Cost Drivers**:
   - ALB: $16/month (fixed)
   - RDS: Check instance size
   - ECS: Check task count and size
   - Data transfer: Check outbound traffic

**Solution:**
- Reduce ECS task count to 1 (dev only)
- Use smaller RDS instance (db.t3.micro)
- Enable RDS auto-pause (dev only)
- Set CloudWatch log retention to 3 days
---

## 💰 Cost Optimization Tips

### Development Environment

```
ECS Tasks: 1 (instead of 2)
RDS: db.t3.micro with auto-pause
ALB: Keep (required)
CloudWatch: 3-day retention
Estimated: $25-35/month
```

### Production Environment

```
ECS Tasks: 2-4 with auto-scaling
RDS: db.t3.small with Multi-AZ
ALB: Keep with HTTPS
CloudWatch: 7-day retention
Estimated: $60-80/month
```

### Cost Monitoring

1. **Set Budget Alert**:
   ```
   AWS Console → Billing → Budgets → Create budget
   Budget type: Cost budget
   Amount: $50/month
   Alert threshold: 80%
   ```

2. **Enable Cost Anomaly Detection**:
   ```
   AWS Console → Cost Explorer → Cost Anomaly Detection
   Create monitor → All AWS services
   ```

---

## 🎓 Learning Resources

### AWS Services Used

1. **VPC** - Networking
   - Docs: https://docs.aws.amazon.com/vpc/
   - Learn: VPC, Subnets, Route Tables, Security Groups

2. **ECS** - Container Orchestration
   - Docs: https://docs.aws.amazon.com/ecs/
   - Learn: Clusters, Services, Tasks, Fargate

3. **RDS** - Managed Database
   - Docs: https://docs.aws.amazon.com/rds/
   - Learn: MySQL, Backups, Security

4. **ECR** - Container Registry
   - Docs: https://docs.aws.amazon.com/ecr/
   - Learn: Repositories, Images, Scanning

5. **ALB** - Load Balancing
   - Docs: https://docs.aws.amazon.com/elasticloadbalancing/
   - Learn: Target Groups, Health Checks, Listeners

6. **CodePipeline** - CI/CD
   - Docs: https://docs.aws.amazon.com/codepipeline/
   - Learn: Pipelines, Stages, Actions

### Next Steps

1. **Add HTTPS**:
   - Request SSL certificate in ACM
   - Add HTTPS listener to ALB
   - Redirect HTTP to HTTPS

2. **Add Custom Domain**:
   - Register domain in Route 53
   - Create A record pointing to ALB
   - Update CORS settings

3. **Enable Auto-Scaling**:
   - Create auto-scaling policy
   - Set target CPU utilization
   - Test scaling behavior

4. **Add Caching**:
   - Create ElastiCache Redis cluster
   - Update application to use cache
   - Reduce database load

5. **Implement Monitoring**:
   - Set up X-Ray tracing
   - Create custom metrics
   - Build comprehensive dashboard

---

## ✅ Deployment Complete!

Congratulations! You've successfully deployed the Singha Loyalty System using AWS Console.

### What You've Learned

✅ VPC networking and subnets
✅ Security groups and network isolation
✅ RDS database setup and configuration
✅ Docker containerization
✅ ECR image management
✅ ECS cluster and service deployment
✅ Application Load Balancer configuration
✅ CloudWatch monitoring and alarms
✅ CI/CD pipeline with CodePipeline
✅ AWS service interconnections

### Your Architecture

```
Internet → ALB → ECS Fargate (2 tasks) → RDS MySQL
                    ↑
                   ECR
                    ↑
            CodePipeline → CodeBuild
                    ↑
                  GitHub
```

### Access Your Application

**API Endpoint**: http://[YOUR-ALB-DNS]
**Health Check**: http://[YOUR-ALB-DNS]/health
**Admin Login**: http://[YOUR-ALB-DNS]/api/admin/login

### Monthly Cost

**Estimated**: $45-62/month
- ECS Fargate Spot: $5-8
- RDS MySQL: $15-20
- ALB: $16
- Other: $10-18

### Support

- **Documentation**: See other .md files in project
- **AWS Support**: https://console.aws.amazon.com/support/
- **Community**: AWS Forums, Stack Overflow

---

**🎉 Well done! Your application is now running on AWS!**
