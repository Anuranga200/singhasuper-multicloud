# Multi-Cloud Disaster Recovery System Architecture

## Table of Contents
1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Traffic Flow](#traffic-flow)
5. [Service Mapping](#service-mapping)
6. [Data Flow](#data-flow)
7. [Failover Architecture](#failover-architecture)

## Overview

The Multi-Cloud Disaster Recovery (DR) system is designed to provide high availability and business continuity across three major cloud providers: AWS (primary), Azure (first failover), and GCP (second failover). The system ensures minimal downtime and data loss through automated failover mechanisms, continuous data replication, and comprehensive health monitoring.

### Key Design Principles

- **Cloud-Agnostic Application**: The application runs identically across all three clouds
- **Active-Passive Configuration**: AWS is active, Azure and GCP are passive standby
- **Automated Failover**: DNS-based failover with health check monitoring
- **Data Replication**: Real-time database replication from primary to all replicas
- **Infrastructure as Code**: All infrastructure defined in Terraform for consistency

### Recovery Objectives

- **RTO (Recovery Time Objective)**: 5 minutes
- **RPO (Recovery Point Objective)**: 1 minute
- **Availability Target**: 99.95% uptime

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Route 53 DNS                                 │
│                    (Health Check Based Routing)                      │
│                                                                       │
│  Primary: AWS → Failover 1: Azure → Failover 2: GCP                 │
└────────────┬────────────────────┬────────────────────┬──────────────┘
             │                    │                    │
             ▼                    ▼                    ▼
    ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
    │   AWS Region   │   │  Azure Region  │   │   GCP Region   │
    │   (Primary)    │   │  (Failover 1)  │   │  (Failover 2)  │
    │                │   │                │   │                │
    │  ┌──────────┐  │   │  ┌──────────┐  │   │  ┌──────────┐  │
    │  │   ALB    │  │   │  │ Azure LB │  │   │  │  GCP LB  │  │
    │  └────┬─────┘  │   │  └────┬─────┘  │   │  └────┬─────┘  │
    │       │        │   │       │        │   │       │        │
    │  ┌────▼─────┐  │   │  ┌────▼─────┐  │   │  ┌────▼─────┐  │
    │  │ EC2 ASG  │  │   │  │ VM Scale │  │   │  │ Instance │  │
    │  │ (t3.micro)│  │   │  │ Set (B1s)│  │   │  │ Group    │  │
    │  └────┬─────┘  │   │  └────┬─────┘  │   │  └────┬─────┘  │
    │       │        │   │       │        │   │       │        │
    │  ┌────▼─────┐  │   │  ┌────▼─────┐  │   │  ┌────▼─────┐  │
    │  │   RDS    │──┼───┼─▶│  Azure   │  │   │  │ Cloud    │  │
    │  │  MySQL   │──┼───┼──┼──────────┼──┼──▶│  SQL      │  │
    │  │ (Primary)│  │   │  │  MySQL   │  │   │  │ MySQL    │  │
    │  │          │  │   │  │ (Replica)│  │   │  │ (Replica)│  │
    │  └──────────┘  │   │  └──────────┘  │   │  └──────────┘  │
    │                │   │                │   │                │
    │  ┌──────────┐  │   │  ┌──────────┐  │   │  ┌──────────┐  │
    │  │ Secrets  │  │   │  │   Key    │  │   │  │  Secret  │  │
    │  │ Manager  │  │   │  │  Vault   │  │   │  │ Manager  │  │
    │  └──────────┘  │   │  └──────────┘  │   │  └──────────┘  │
    └────────────────┘   └────────────────┘   └────────────────┘
```

## Component Architecture

### 1. DNS and Traffic Management

**Route 53 (AWS)**
- Manages global DNS for the application domain
- Implements health check-based failover routing
- Health checks run every 30 seconds against all cloud endpoints
- TTL set to 60 seconds for fast failover propagation

**Failover Policy**:
1. Primary: AWS ALB endpoint
2. Secondary: Azure Load Balancer endpoint
3. Tertiary: GCP Load Balancer endpoint

### 2. Compute Layer

#### AWS (Primary)
- **Service**: EC2 Auto Scaling Group
- **Instance Type**: t3.micro
- **Configuration**:
  - Min: 2 instances
  - Max: 10 instances
  - Desired: 2 instances
  - Scaling based on CPU utilization (>70%)
- **Deployment**: Docker containers via user data script
- **Availability**: Multi-AZ deployment across 2 availability zones

#### Azure (Failover 1)
- **Service**: Virtual Machine Scale Set (VMSS)
- **Instance Type**: B1s
- **Configuration**:
  - Min: 2 instances
  - Max: 10 instances
  - Desired: 2 instances
  - Scaling based on CPU percentage (>70%)
- **Deployment**: Docker containers via custom script extension
- **Availability**: Zone-redundant deployment

#### GCP (Failover 2)
- **Service**: Managed Instance Group
- **Instance Type**: e2-micro
- **Configuration**:
  - Min: 2 instances
  - Max: 10 instances
  - Target CPU: 70%
- **Deployment**: Docker containers via startup script
- **Availability**: Multi-zone deployment

### 3. Load Balancing

#### AWS Application Load Balancer
- **Type**: Application Load Balancer (Layer 7)
- **Scheme**: Internet-facing
- **Health Check**:
  - Path: `/health`
  - Interval: 30 seconds
  - Timeout: 5 seconds
  - Healthy threshold: 2
  - Unhealthy threshold: 3
- **SSL/TLS**: TLS 1.2+ enforced
- **Listeners**: HTTPS (443)

#### Azure Load Balancer
- **Type**: Standard Load Balancer
- **SKU**: Standard
- **Health Probe**:
  - Protocol: HTTP
  - Path: `/health`
  - Interval: 30 seconds
- **SSL/TLS**: TLS 1.2+ enforced
- **Frontend**: Public IP with DNS label

#### GCP Load Balancer
- **Type**: HTTP(S) Load Balancer
- **Health Check**:
  - Path: `/health`
  - Check interval: 30 seconds
  - Timeout: 5 seconds
  - Healthy threshold: 2
  - Unhealthy threshold: 3
- **SSL/TLS**: TLS 1.2+ enforced
- **Backend Service**: Instance group backend

### 4. Database Layer

#### AWS RDS MySQL (Primary)
- **Engine**: MySQL 8.0
- **Instance Class**: db.t3.micro
- **Storage**: 20 GB GP2
- **Configuration**:
  - Multi-AZ: Enabled (local HA)
  - Binary logging: Enabled (for replication)
  - Automated backups: 30-day retention
  - Point-in-time recovery: 7 days
  - Encryption at rest: Enabled
  - Encryption in transit: TLS enforced

#### Azure Database for MySQL (Replica)
- **Tier**: Basic
- **Compute**: 1 vCore
- **Storage**: 20 GB
- **Configuration**:
  - Replication: Binary log replication from AWS RDS
  - Geo-redundant backup: Enabled
  - SSL enforcement: Required
  - Encryption at rest: Enabled

#### GCP Cloud SQL MySQL (Replica)
- **Tier**: db-f1-micro
- **Storage**: 20 GB SSD
- **Configuration**:
  - Replication: Binary log replication from AWS RDS
  - Automated backups: Daily
  - High availability: Regional (standby)
  - SSL enforcement: Required
  - Encryption at rest: Enabled

### 5. Secrets Management

#### AWS Secrets Manager
- Stores database credentials
- Stores JWT secrets and API keys
- Automatic rotation: 90 days
- Encryption: AWS KMS

#### Azure Key Vault
- Stores database credentials
- Stores application secrets
- Access policies: VM managed identities
- Encryption: Azure-managed keys

#### GCP Secret Manager
- Stores database credentials
- Stores application secrets
- IAM bindings: Compute service accounts
- Encryption: Google-managed keys

### 6. Networking

#### AWS VPC
- **CIDR**: 10.0.0.0/16
- **Subnets**:
  - Public: 10.0.1.0/24, 10.0.2.0/24 (2 AZs)
  - Private: 10.0.11.0/24, 10.0.12.0/24 (2 AZs)
- **Components**:
  - Internet Gateway
  - NAT Gateway (per AZ)
  - Route tables
  - Security groups

#### Azure Virtual Network
- **Address Space**: 10.1.0.0/16
- **Subnets**:
  - Public: 10.1.1.0/24
  - Private: 10.1.11.0/24
- **Components**:
  - Network Security Groups
  - Route tables
  - NAT Gateway

#### GCP VPC Network
- **Subnet Mode**: Custom
- **Subnets**:
  - Public: 10.2.1.0/24
  - Private: 10.2.11.0/24
- **Components**:
  - Firewall rules
  - Cloud NAT
  - Cloud Router

## Traffic Flow

### Normal Operation (AWS Active)

```
User Request
    │
    ▼
Route 53 DNS Resolution
    │
    ├─ Health Check: AWS ✓ (Healthy)
    │
    ▼
AWS ALB (Public IP)
    │
    ├─ SSL Termination
    ├─ Health Check: /health
    │
    ▼
EC2 Instance (Private Subnet)
    │
    ├─ Docker Container
    ├─ Application Logic
    │
    ▼
RDS MySQL (Private Subnet)
    │
    ├─ Read/Write Operations
    ├─ Binary Log Replication ──┬──▶ Azure MySQL (Read Replica)
    │                            │
    │                            └──▶ GCP Cloud SQL (Read Replica)
    ▼
Response to User
```

### Failover State (Azure Active)

```
User Request
    │
    ▼
Route 53 DNS Resolution
    │
    ├─ Health Check: AWS ✗ (Unhealthy)
    ├─ Health Check: Azure ✓ (Healthy)
    │
    ▼
Azure Load Balancer (Public IP)
    │
    ├─ SSL Termination
    ├─ Health Probe: /health
    │
    ▼
Azure VM (Private Subnet)
    │
    ├─ Docker Container
    ├─ Application Logic
    │
    ▼
Azure MySQL (Promoted to Primary)
    │
    ├─ Read/Write Operations
    ├─ Replication Stopped
    │
    ▼
Response to User
```

### Cascade Failover (GCP Active)

```
User Request
    │
    ▼
Route 53 DNS Resolution
    │
    ├─ Health Check: AWS ✗ (Unhealthy)
    ├─ Health Check: Azure ✗ (Unhealthy)
    ├─ Health Check: GCP ✓ (Healthy)
    │
    ▼
GCP Load Balancer (Public IP)
    │
    ├─ SSL Termination
    ├─ Health Check: /health
    │
    ▼
GCP Compute Instance (Private Subnet)
    │
    ├─ Docker Container
    ├─ Application Logic
    │
    ▼
Cloud SQL MySQL (Promoted to Primary)
    │
    ├─ Read/Write Operations
    ├─ Replication Stopped
    │
    ▼
Response to User
```

## Service Mapping

### Cross-Cloud Service Equivalents

| Function | AWS | Azure | GCP |
|----------|-----|-------|-----|
| **Compute** | EC2 Auto Scaling Group | VM Scale Set | Managed Instance Group |
| **Load Balancer** | Application Load Balancer | Standard Load Balancer | HTTP(S) Load Balancer |
| **Database** | RDS MySQL | Azure Database for MySQL | Cloud SQL MySQL |
| **Secrets** | Secrets Manager | Key Vault | Secret Manager |
| **Networking** | VPC | Virtual Network | VPC Network |
| **DNS** | Route 53 | Azure DNS | Cloud DNS |
| **Monitoring** | CloudWatch | Azure Monitor | Cloud Monitoring |
| **IAM** | IAM Roles | Managed Identities | Service Accounts |

### Port Mappings

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Load Balancer | 443 | HTTPS | Application traffic |
| Load Balancer | 80 | HTTP | Redirect to HTTPS |
| Application | 3000 | HTTP | Internal application port |
| MySQL | 3306 | TCP | Database connections |
| Health Check | 3000 | HTTP | `/health` endpoint |

## Data Flow

### Database Replication Flow

```
AWS RDS MySQL (Primary)
    │
    ├─ Binary Logs Generated
    │
    ├─ Replication User: replication_user
    │
    ├──────────────────────────────────┐
    │                                   │
    ▼                                   ▼
Azure MySQL Replica              GCP Cloud SQL Replica
    │                                   │
    ├─ Replication Lag: <30s            ├─ Replication Lag: <30s
    ├─ Read-Only Mode                   ├─ Read-Only Mode
    │                                   │
    ▼                                   ▼
Standby for Failover            Standby for Failover
```

### Backup Flow

```
Primary Database (AWS RDS)
    │
    ├─ Automated Daily Backup (30-day retention)
    ├─ Point-in-Time Recovery (7 days)
    │
    ▼
S3 Backup Storage (Cross-Region)

Replica Databases (Azure, GCP)
    │
    ├─ Independent Backup Schedule
    ├─ Geo-Redundant Storage
    │
    ▼
Cloud-Native Backup Storage
```

### Secrets Synchronization

```
Manual Secret Creation
    │
    ├─ AWS Secrets Manager
    ├─ Azure Key Vault
    ├─ GCP Secret Manager
    │
    ▼
Application Retrieval at Runtime
    │
    ├─ IAM Role (AWS)
    ├─ Managed Identity (Azure)
    ├─ Service Account (GCP)
```

## Failover Architecture

### Automated Failover Process

```
┌─────────────────────────────────────────────────────────────┐
│                    Health Monitor Service                    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AWS Health   │  │ Azure Health │  │ GCP Health   │      │
│  │ Check (30s)  │  │ Check (30s)  │  │ Check (30s)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Failure        │
                    │ Detected?      │
                    └────────┬───────┘
                             │
                    Yes      │
                             ▼
                    ┌────────────────┐
                    │ Consecutive    │
                    │ Failures >= 3? │
                    └────────┬───────┘
                             │
                    Yes      │
                             ▼
                    ┌────────────────────┐
                    │ Failover           │
                    │ Orchestrator       │
                    └────────┬───────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌───────────────────┐     ┌───────────────────┐
    │ Verify Target     │     │ Promote Database  │
    │ Cloud Health      │     │ Replica           │
    └─────────┬─────────┘     └─────────┬─────────┘
              │                         │
              └────────────┬────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Update DNS Records   │
                │ (Route 53)           │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Send Notifications   │
                │ (Email, SMS, Logs)   │
                └──────────────────────┘
```

### Failover Decision Matrix

| AWS Status | Azure Status | GCP Status | Active Cloud | Action |
|------------|--------------|------------|--------------|--------|
| Healthy | Any | Any | AWS | Normal operation |
| Unhealthy | Healthy | Any | Azure | Failover to Azure |
| Unhealthy | Unhealthy | Healthy | GCP | Failover to GCP |
| Unhealthy | Unhealthy | Unhealthy | None | Critical alert |

### Database Promotion Process

1. **Stop Replication**: `STOP SLAVE;` on target replica
2. **Reset Slave Info**: `RESET SLAVE ALL;`
3. **Verify Data Integrity**: Check replication lag = 0
4. **Enable Writes**: Remove read-only mode
5. **Update Application Config**: Point to new primary endpoint
6. **Verify Connectivity**: Test write operations

## Monitoring and Observability

### Metrics Collection

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Dashboard                         │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AWS          │  │ Azure        │  │ GCP          │      │
│  │ CloudWatch   │  │ Monitor      │  │ Cloud        │      │
│  │              │  │              │  │ Monitoring   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│                  ┌──────────────────┐                        │
│                  │ Aggregated       │                        │
│                  │ Metrics          │                        │
│                  │                  │                        │
│                  │ - System Health  │                        │
│                  │ - RTO/RPO        │                        │
│                  │ - Replication    │                        │
│                  │ - Costs          │                        │
│                  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Metrics

- **Application Health**: HTTP response time, error rate, request count
- **Database Health**: Replication lag, connection count, query performance
- **Infrastructure Health**: CPU, memory, disk, network utilization
- **Failover Metrics**: RTO, RPO, failover count, failback success rate
- **Cost Metrics**: Per-cloud spend, total spend, budget utilization

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                                    │
│ - Security Groups / NSGs / Firewall Rules                    │
│ - Private Subnets for Databases                              │
│ - TLS 1.2+ Enforcement                                       │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Identity and Access Management                      │
│ - IAM Roles / Managed Identities / Service Accounts         │
│ - Least Privilege Policies                                   │
│ - No Long-Term Credentials                                   │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Data Protection                                     │
│ - Encryption at Rest (Database, Backups)                     │
│ - Encryption in Transit (TLS)                                │
│ - Secrets Management (No Hardcoded Credentials)             │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Application Security                                │
│ - Input Validation                                           │
│ - Authentication and Authorization                           │
│ - Security Headers                                           │
└─────────────────────────────────────────────────────────────┘
```

### Credential Management

- **No Hardcoded Secrets**: All credentials stored in cloud-native secret managers
- **Automatic Rotation**: Database credentials rotated every 90 days
- **Runtime Retrieval**: Applications fetch secrets at startup using IAM roles
- **Audit Logging**: All secret access logged and monitored

## Disaster Recovery Scenarios

### Scenario 1: AWS Region Failure

**Detection**: Health checks fail for 90 seconds (3 consecutive failures)

**Response**:
1. Failover orchestrator triggers Azure failover
2. Azure MySQL replica promoted to primary
3. Route 53 updates DNS to Azure endpoint
4. Notifications sent to operations team

**Recovery Time**: ~3-5 minutes
**Data Loss**: <1 minute (replication lag)

### Scenario 2: Database Corruption

**Detection**: Data consistency checks fail

**Response**:
1. Stop application writes
2. Identify last known good backup
3. Restore from backup to new instance
4. Verify data integrity
5. Update application configuration
6. Resume operations

**Recovery Time**: ~15-30 minutes (depends on backup size)
**Data Loss**: Up to last backup point

### Scenario 3: Complete AWS and Azure Failure

**Detection**: Health checks fail for both AWS and Azure

**Response**:
1. Failover orchestrator triggers GCP failover
2. GCP Cloud SQL replica promoted to primary
3. Route 53 updates DNS to GCP endpoint
4. Critical alert sent to operations team

**Recovery Time**: ~5-7 minutes
**Data Loss**: <1 minute (replication lag)

## Conclusion

This architecture provides a robust, multi-cloud disaster recovery solution with automated failover, continuous data replication, and comprehensive monitoring. The system is designed to meet strict RTO and RPO requirements while maintaining cost efficiency through the use of appropriately sized resources and automated management.

For operational procedures, refer to the runbooks in the `docs/runbooks/` directory.
