# Local Testing & ECS Troubleshooting Guide

## 🎯 Overview

This guide helps you:
1. Test the application locally with Docker
2. Verify all components work correctly
3. Troubleshoot the ECS Circuit Breaker error
4. Fix deployment issues

**Estimated Time:** 30-45 minutes

---

## Part 1: Local Environment Setup (10 minutes)

### Step 1.1: Verify Prerequisites

Check that you have everything installed:

```bash
# Check Node.js version (should be 18+)
node --version

# Check npm version
npm --version

# Check Docker version
docker --version

# Check Docker is running
docker ps
```

**Expected Output:**
- Node: v18.x.x or higher
- npm: 9.x.x or higher
- Docker: 20.x.x or higher
- docker ps: Should show running containers or empty list (no errors)

**If any command fails:**
- Node.js: Download from https://nodejs.org/
- Docker: Download from https://www.docker.com/products/docker-desktop/

---

### Step 1.2: Navigate to Server Directory

```bash
# From project root
cd server

# Verify you're in the right place
ls
```

**Expected Output:**
You should see:
- package.json
- Dockerfile
- src/
- .env.example

---

### Step 1.3: Create Local Environment File

```bash
# Copy example environment file
cp .env.example .env
```

Now edit the `.env` file with your text editor.

**Open:** `server/.env`

**Replace with your actual values:**

```env
# Server Configuration
NODE_ENV=development
PORT=3000

# Database Configuration (Use your RDS endpoint)
DB_HOST=singha-loyalty-db.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=YourActualPassword
DB_NAME=singha_loyalty

# JWT Configuration (Generate random strings)
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_REFRESH_SECRET=your-super-secret-refresh-key-min-32-chars

# CORS Configuration
CORS_ORIGIN=*
```

**⚠️ IMPORTANT:**
- Replace `DB_HOST` with your actual RDS endpoint
- Replace `DB_PASSWORD` with your actual RDS password
- Generate strong random strings for JWT secrets

**To generate JWT secrets:**
```bash
# On Windows (PowerShell)
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# On Linux/Mac
openssl rand -base64 32
```

---

## Part 2: Test Without Docker (15 minutes)

### Step 2.1: Install Dependencies

```bash
# Make sure you're in server/ directory
npm install
```

**Wait for installation to complete** (2-3 minutes)

**Expected Output:**
```
added XXX packages in XXs
```

**If you see errors:**
- Check your internet connection
- Try: `npm cache clean --force` then `npm install` again

---

### Step 2.2: Test Database Connection

Before running the app, verify database connectivity:

```bash
# Run the migration script (this will test connection)
npm run migrate
```

**Expected Output:**
```
🔄 Starting database migration...
✅ Database connected successfully
✅ Migration completed successfully
```

**If you see errors:**

**Error: "ECONNREFUSED" or "ETIMEDOUT"**
- Your RDS endpoint is wrong or unreachable
- Check Security Group allows your IP
- Verify RDS is in "Available" state

**Error: "Access denied for user"**
- Wrong DB_USER or DB_PASSWORD
- Check credentials in .env file

**Error: "Unknown database"**
- Database name is wrong
- Check DB_NAME in .env file

**To fix Security Group (if connection refused):**
1. Go to AWS Console → RDS → Databases → singha-loyalty-db
2. Click on VPC security group
3. Edit inbound rules
4. Add rule: Type=MySQL/Aurora, Port=3306, Source=My IP
5. Save rules
6. Try `npm run migrate` again

---

### Step 2.3: Seed Database

```bash
npm run seed
```

**Expected Output:**
```
🌱 Starting database seeding...
✅ Database connected successfully
✅ Admin user created: admin@singha.com
✅ Sample customers created
✅ Seeding completed successfully
```

---

### Step 2.4: Start Application Locally

```bash
npm start
```

**Expected Output:**
```
🚀 Server running on port 3000
📊 Environment: development
✅ Database connected successfully
```

**Keep this terminal open!** The server is now running.

---

### Step 2.5: Test Endpoints (New Terminal)

Open a **NEW terminal window** and run these tests:

**Test 1: Health Check**
```bash
curl http://localhost:3000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T...",
  "uptime": 5.123,
  "database": "connected"
}
```

**Test 2: Customer Registration**
```bash
curl -X POST http://localhost:3000/api/customers/register -H "Content-Type: application/json" -d "{\"nicNumber\":\"999888777V\",\"fullName\":\"Test User\",\"phoneNumber\":\"0771234567\"}"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Registration successful",
  "loyaltyNumber": "SL-XXXX"
}
```

**Test 3: Admin Login**
```bash
curl -X POST http://localhost:3000/api/admin/login -H "Content-Type: application/json" -d "{\"email\":\"admin@singha.com\",\"password\":\"Admin@123\"}"
```

**Expected Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "admin": {
    "id": 1,
    "email": "admin@singha.com",
    "name": "System Administrator"
  }
}
```

**Test 4: Get Customers (Protected Route)**

First, copy the token from Test 3, then:

```bash
# Replace YOUR_TOKEN_HERE with actual token
curl http://localhost:3000/api/customers -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response:**
```json
{
  "customers": [...],
  "count": 1,
  "page": 1,
  "totalPages": 1
}
```

---

### Step 2.6: Verify All Tests Pass

**✅ Checklist:**
- [ ] Health check returns 200 OK
- [ ] Customer registration works
- [ ] Admin login returns token
- [ ] Protected route works with token
- [ ] No errors in server terminal

**If all tests pass:** Your application code is working correctly! The issue is with Docker or ECS configuration.

**If tests fail:** Fix the application code before proceeding to Docker testing.

---

## Part 3: Test With Docker Locally (15 minutes)

Now let's test the exact same Docker image that will run on ECS.

### Step 3.1: Stop the Running Server

Go back to the terminal where `npm start` is running and press:
```
Ctrl + C
```

---

### Step 3.2: Review Dockerfile

Open `server/Dockerfile` and verify it looks correct:

```bash
# View Dockerfile
cat Dockerfile
```

**Expected Content:**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "src/index.js"]
```

**Common Issues to Check:**
- ✅ Uses `node:18-alpine` (lightweight)
- ✅ Copies package files first (for caching)
- ✅ Uses `npm ci` (faster, more reliable)
- ✅ Exposes port 3000
- ✅ Runs `node src/index.js`

---

### Step 3.3: Build Docker Image

```bash
# Build the image (this takes 2-3 minutes)
docker build -t singha-loyalty-test:latest .
```

**Expected Output:**
```
[+] Building 45.2s (10/10) FINISHED
 => [internal] load build definition
 => [internal] load .dockerignore
 => [1/5] FROM docker.io/library/node:18-alpine
 => [2/5] WORKDIR /app
 => [3/5] COPY package*.json ./
 => [4/5] RUN npm ci --only=production
 => [5/5] COPY . .
 => exporting to image
 => => naming to docker.io/library/singha-loyalty-test:latest
```

**If build fails:**
- Check Dockerfile syntax
- Ensure package.json exists
- Check for .dockerignore issues

---

### Step 3.4: Run Docker Container Locally

```bash
# Run container with environment variables
docker run -d \
  --name singha-test \
  -p 3000:3000 \
  -e NODE_ENV=production \
  -e PORT=3000 \
  -e DB_HOST=singha-loyalty-db.xxxxx.us-east-1.rds.amazonaws.com \
  -e DB_PORT=3306 \
  -e DB_USER=admin \
  -e DB_PASSWORD=YourActualPassword \
  -e DB_NAME=singha_loyalty \
  -e JWT_SECRET=your-super-secret-jwt-key-min-32-chars \
  -e JWT_REFRESH_SECRET=your-super-secret-refresh-key-min-32-chars \
  -e CORS_ORIGIN=* \
  singha-loyalty-test:latest
```

**⚠️ IMPORTANT:** Replace the environment variable values with your actual values!

**Expected Output:**
```
a1b2c3d4e5f6... (container ID)
```

---

### Step 3.5: Check Container Status

```bash
# Check if container is running
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE                        STATUS         PORTS
a1b2c3d4e5f6   singha-loyalty-test:latest   Up 5 seconds   0.0.0.0:3000->3000/tcp
```

**If container is not listed:**
```bash
# Check stopped containers
docker ps -a
```

**If STATUS shows "Exited":**
```bash
# View container logs to see why it crashed
docker logs singha-test
```

---

### Step 3.6: View Container Logs

```bash
# View real-time logs
docker logs -f singha-test
```

**Expected Output:**
```
🚀 Server running on port 3000
📊 Environment: production
✅ Database connected successfully
```

**Press Ctrl+C to stop viewing logs** (container keeps running)

**If you see errors:**

**Error: "Database connection failed"**
- Container can't reach RDS
- Check DB_HOST is correct
- Check Security Group allows container's IP

**Error: "JWT_SECRET is required"**
- Environment variables not passed correctly
- Check docker run command has all -e flags

**Error: "Port 3000 is already in use"**
- Stop the npm start server first
- Or use different port: `-p 3001:3000`

---

### Step 3.7: Test Docker Container

Run the same tests as before:

**Test 1: Health Check**
```bash
curl http://localhost:3000/health
```

**Test 2: Customer Registration**
```bash
curl -X POST http://localhost:3000/api/customers/register -H "Content-Type: application/json" -d "{\"nicNumber\":\"888777666V\",\"fullName\":\"Docker Test\",\"phoneNumber\":\"0771234568\"}"
```

**Test 3: Admin Login**
```bash
curl -X POST http://localhost:3000/api/admin/login -H "Content-Type: application/json" -d "{\"email\":\"admin@singha.com\",\"password\":\"Admin@123\"}"
```

---

### Step 3.8: Verify Docker Tests Pass

**✅ Checklist:**
- [ ] Container starts successfully
- [ ] Container stays running (doesn't crash)
- [ ] Health check returns 200 OK
- [ ] All API endpoints work
- [ ] Logs show "Database connected successfully"

**If all tests pass:** Your Docker image is working correctly! The issue is with ECS configuration.

---

### Step 3.9: Clean Up

```bash
# Stop and remove test container
docker stop singha-test
docker rm singha-test

# Optional: Remove test image
docker rmi singha-loyalty-test:latest
```

---

## Part 4: Troubleshoot ECS Circuit Breaker (20 minutes)

The Circuit Breaker error means ECS tried to deploy your container but it failed health checks or crashed repeatedly.

### Step 4.1: Check ECS Service Events

1. Go to **AWS Console** → **ECS**
2. Click **Clusters** → **singha-loyalty-cluster**
3. Click **Services** → **singha-loyalty-service**
4. Click **Events** tab

**Look for error messages like:**
- "service singha-loyalty-service was unable to place a task"
- "Task failed container health checks"
- "Task stopped with exit code 1"
- "Essential container exited"

**Copy the error messages** - we'll use them to diagnose the issue.

---

### Step 4.2: Check Task Logs in CloudWatch

1. Go to **CloudWatch** → **Log groups**
2. Click `/ecs/singha-loyalty`
3. Click on the **most recent log stream**

**Look for:**
- ✅ "Server running on port 3000" - Good!
- ✅ "Database connected successfully" - Good!
- ❌ "Database connection failed" - Problem!
- ❌ "Error: ..." - Problem!
- ❌ No logs at all - Container crashed immediately

**Copy any error messages** you see.

---

### Step 4.3: Check Task Definition

1. Go to **ECS** → **Task definitions**
2. Click **singha-loyalty-task**
3. Click on the **latest revision**
4. Review the configuration

**Common Issues:**

**Issue 1: Wrong Image URI**
- Check: Container image URI
- Should be: `123456789.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest`
- Verify: Account ID, region, repository name are correct

**Issue 2: Wrong Port Mapping**
- Check: Port mappings
- Should be: Container port = 3000, Protocol = TCP

**Issue 3: Missing Environment Variables**
- Check: Environment variables section
- Required variables:
  - NODE_ENV=production
  - PORT=3000
  - DB_HOST=your-rds-endpoint
  - DB_PORT=3306
  - DB_USER=admin
  - DB_PASSWORD=your-password
  - DB_NAME=singha_loyalty
  - JWT_SECRET=your-secret
  - JWT_REFRESH_SECRET=your-secret
  - CORS_ORIGIN=*

**Issue 4: Wrong Task Execution Role**
- Check: Task execution role
- Should be: singha-ecs-task-execution-role
- This role needs: AmazonECSTaskExecutionRolePolicy

---

### Step 4.4: Check Security Groups

**ECS Security Group:**
1. Go to **EC2** → **Security Groups**
2. Find **singha-ecs-sg**
3. Click **Inbound rules**

**Should have:**
- Type: Custom TCP
- Port: 3000
- Source: singha-alb-sg (the ALB security group ID)

**Should also have:**
- Type: All traffic
- Source: 0.0.0.0/0 (for outbound to RDS)

**Or add outbound rule:**
4. Click **Outbound rules** → **Edit outbound rules**
5. Should have: All traffic to 0.0.0.0/0

**RDS Security Group:**
1. Find **singha-rds-sg**
2. Click **Inbound rules**

**Should have:**
- Type: MySQL/Aurora
- Port: 3306
- Source: singha-ecs-sg (the ECS security group ID)

---

### Step 4.5: Check Target Group Health Check

1. Go to **EC2** → **Target Groups**
2. Click **singha-loyalty-tg**
3. Click **Health checks** tab

**Verify settings:**
- Health check protocol: HTTP
- Health check path: `/health`
- Port: Traffic port
- Healthy threshold: 2
- Unhealthy threshold: 3
- Timeout: 5 seconds
- Interval: 30 seconds
- Success codes: 200

**If path is wrong:**
1. Click **Edit**
2. Change Health check path to: `/health`
3. Click **Save changes**

---

### Step 4.6: Check ECS Service Configuration

1. Go to **ECS** → **Clusters** → **singha-loyalty-cluster**
2. Click **singha-loyalty-service**
3. Click **Configuration and networking** tab

**Verify:**
- Launch type: FARGATE
- Platform version: LATEST
- Subnets: Both public subnets selected
- Security groups: singha-ecs-sg
- Public IP: ENABLED (important!)
- Load balancer: singha-loyalty-alb
- Target group: singha-loyalty-tg
- Health check grace period: 60 seconds (or higher)

**If Public IP is DISABLED:**
- This is likely the problem!
- Tasks can't reach RDS or pull from ECR
- You need to recreate the service with Public IP enabled

---

## Part 5: Fix Common ECS Issues

### Fix 1: Recreate Task Definition with Correct Settings

If you found issues in Step 4.3:

1. Go to **ECS** → **Task definitions** → **singha-loyalty-task**
2. Select latest revision → **Create new revision**
3. **Fix the issues you found:**
   - Correct image URI
   - Add missing environment variables
   - Fix port mappings
   - Select correct IAM roles
4. Click **Create**

5. **Update the service to use new revision:**
   - Go to **Clusters** → **singha-loyalty-cluster**
   - Click **singha-loyalty-service**
   - Click **Update service**
   - Force new deployment: ☑ (check this)
   - Click **Update**

---

### Fix 2: Increase Health Check Grace Period

If tasks are starting but failing health checks too quickly:

1. Go to **ECS** → **Clusters** → **singha-loyalty-cluster**
2. Click **singha-loyalty-service**
3. Click **Update service**
4. Scroll to **Load balancing**
5. Change **Health check grace period** to: **120 seconds**
6. Click **Update**

This gives your container more time to start before health checks begin.

---

### Fix 3: Enable Public IP (If Disabled)

If Public IP is disabled, you need to recreate the service:

1. **Delete the existing service:**
   - Go to **ECS** → **Clusters** → **singha-loyalty-cluster**
   - Click **singha-loyalty-service**
   - Click **Delete service**
   - Type "delete" to confirm
   - Click **Delete**

2. **Create new service with Public IP enabled:**
   - Follow Step 6.3 from CONSOLE_DEPLOYMENT_GUIDE.md
   - Make sure to select **Public IP: ENABLED**

---

### Fix 4: Fix Security Group Rules

If security groups are wrong:

**For ECS Security Group:**
1. Go to **EC2** → **Security Groups** → **singha-ecs-sg**
2. **Inbound rules** → **Edit inbound rules**
3. Ensure rule exists:
   - Type: Custom TCP
   - Port: 3000
   - Source: [singha-alb-sg ID]
4. **Outbound rules** → **Edit outbound rules**
5. Ensure rule exists:
   - Type: All traffic
   - Destination: 0.0.0.0/0
6. Click **Save rules**

**For RDS Security Group:**
1. Go to **EC2** → **Security Groups** → **singha-rds-sg**
2. **Inbound rules** → **Edit inbound rules**
3. Ensure rule exists:
   - Type: MySQL/Aurora
   - Port: 3306
   - Source: [singha-ecs-sg ID]
4. Click **Save rules**

---

### Fix 5: Verify ECR Image Exists

1. Go to **ECR** → **Repositories** → **singha-loyalty**
2. Verify you see an image with tag **latest**
3. Note the **Image URI**

**If no image exists:**
```bash
# Push image again (from server/ directory)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 285229572166.dkr.ecr.us-east-1.amazonaws.com

docker build -t singha-loyalty:latest .

docker tag singha-loyalty:latest 285229572166.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest

docker push 285229572166.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest
```

---

## Part 6: Monitor Deployment

After making fixes, monitor the deployment:

### Step 6.1: Watch Service Events

1. Go to **ECS** → **Clusters** → **singha-loyalty-cluster**
2. Click **singha-loyalty-service**
3. Click **Events** tab
4. Click refresh button every 30 seconds

**Look for:**
- ✅ "service singha-loyalty-service has reached a steady state"
- ✅ "service singha-loyalty-service has started 2 tasks"
- ❌ "service singha-loyalty-service was unable to place a task"

---

### Step 6.2: Watch Task Status

1. Click **Tasks** tab
2. Watch task status change:
   - PROVISIONING → PENDING → RUNNING

**If task shows RUNNING:**
3. Wait 60-120 seconds for health checks
4. Check **Health status** column
5. Should change to: HEALTHY

**If task stops:**
6. Click on the stopped task
7. Look at **Stopped reason**
8. Check **Containers** section for exit code

---

### Step 6.3: Watch CloudWatch Logs

1. Go to **CloudWatch** → **Log groups** → `/ecs/singha-loyalty`
2. Click on newest log stream
3. Click **Refresh** button

**Expected logs:**
```
🚀 Server running on port 3000
📊 Environment: production
✅ Database connected successfully
```

---

### Step 6.4: Check Target Group

1. Go to **EC2** → **Target Groups** → **singha-loyalty-tg**
2. Click **Targets** tab
3. Wait for targets to appear
4. Watch **Health status** change:
   - initial → unhealthy → healthy

**This can take 2-3 minutes**

---

### Step 6.5: Test the Deployment

Once targets are healthy:

```bash
# Get your ALB DNS name
# AWS Console → EC2 → Load Balancers → singha-loyalty-alb → DNS name

# Test health check
curl http://[YOUR-ALB-DNS]/health

# Test customer registration
curl -X POST http://[YOUR-ALB-DNS]/api/customers/register -H "Content-Type: application/json" -d "{\"nicNumber\":\"777666555V\",\"fullName\":\"ECS Test\",\"phoneNumber\":\"0771234569\"}"
```

---

## Part 7: Common Error Solutions

### Error: "CannotPullContainerError"

**Cause:** ECS can't pull image from ECR

**Solution:**
1. Verify image exists in ECR
2. Check task execution role has `AmazonECSTaskExecutionRolePolicy`
3. Verify image URI in task definition is correct

---

### Error: "ResourceInitializationError: unable to pull secrets or registry auth"

**Cause:** IAM permissions issue

**Solution:**
1. Go to **IAM** → **Roles** → **singha-ecs-task-execution-role**
2. Click **Attach policies**
3. Search and attach: `AmazonECSTaskExecutionRolePolicy`
4. Click **Attach policy**

---

### Error: "Task failed to start"

**Cause:** Container crashes immediately

**Solution:**
1. Check CloudWatch logs for error message
2. Verify environment variables are correct
3. Test Docker image locally (Part 3)

---

### Error: "Health checks failed"

**Cause:** Container running but /health endpoint not responding

**Solution:**
1. Verify health check path is `/health` (not `/api/health`)
2. Increase health check grace period to 120 seconds
3. Check container logs - is server actually starting?
4. Verify port 3000 is exposed in Dockerfile

---

### Error: "Database connection failed"

**Cause:** Container can't reach RDS

**Solution:**
1. Verify Public IP is ENABLED on ECS service
2. Check RDS security group allows traffic from ECS security group
3. Verify DB_HOST environment variable is correct RDS endpoint
4. Check RDS is in "Available" state

---

## ✅ Success Checklist

Your deployment is successful when:

- [ ] ECS service shows "RUNNING" status
- [ ] 2 tasks are running and healthy
- [ ] Target group shows 2 healthy targets
- [ ] CloudWatch logs show "Database connected successfully"
- [ ] Health check endpoint returns 200 OK
- [ ] Customer registration works via ALB
- [ ] Admin login works via ALB
- [ ] No errors in service events

---

## 📞 Still Having Issues?

If you're still stuck after following this guide:

1. **Collect this information:**
   - ECS service events (last 10 events)
   - CloudWatch logs (last 50 lines)
   - Task stopped reason (if applicable)
   - Target group health status
   - Security group configurations

2. **Double-check:**
   - All environment variables are set correctly
   - RDS endpoint is correct
   - Security groups allow traffic flow
   - Public IP is enabled
   - Image exists in ECR

3. **Try the nuclear option:**
   - Delete the ECS service
   - Delete the task definition
   - Start fresh from Step 6.2 in CONSOLE_DEPLOYMENT_GUIDE.md
   - Follow each step carefully

---

**Good luck! 🚀**
