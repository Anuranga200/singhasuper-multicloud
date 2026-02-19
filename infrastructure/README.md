# Multi-Cloud Disaster Recovery Infrastructure

This directory contains all infrastructure code, automation scripts, and documentation for the multi-cloud DR system.

## Directory Structure

```
infrastructure/
├── terraform/              # Infrastructure as Code
│   ├── aws/               # AWS primary cloud modules
│   ├── azure/             # Azure failover cloud modules
│   ├── gcp/               # GCP failover cloud modules
│   └── modules/           # Shared Terraform modules
├── scripts/               # Python automation scripts
│   ├── monitoring/        # Health monitoring and alerting
│   ├── failover/          # Failover orchestration
│   ├── replication/       # Database replication management
│   ├── cost/              # Cost monitoring and reporting
│   └── backup/            # Backup and recovery automation
├── tests/                 # Test suites
│   ├── unit/             # Unit tests
│   ├── property/         # Property-based tests
│   └── integration/      # Integration tests
├── docs/                  # Documentation and runbooks
│   ├── architecture/     # Architecture diagrams and docs
│   ├── deployment/       # Deployment guides
│   ├── runbooks/         # Operational runbooks
│   └── troubleshooting/  # Troubleshooting guides
└── .github/              # CI/CD workflows
    └── workflows/        # GitHub Actions workflows
```

## Quick Start

### Prerequisites

- Terraform >= 1.5.0
- Python >= 3.10
- AWS CLI configured
- Azure CLI configured
- gcloud CLI configured

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize Terraform
cd terraform/aws && terraform init
cd terraform/azure && terraform init
cd terraform/gcp && terraform init
```

### Deployment

See `docs/deployment/` for detailed deployment guides for each cloud provider.

## Cost Estimation

- AWS (Primary): ~$76/month
- Azure (Failover): ~$70/month
- GCP (Failover): ~$60/month
- **Total: ~$206/month**

## Support

For issues or questions, refer to the troubleshooting guides in `docs/troubleshooting/`.
