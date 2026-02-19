# CI/CD Workflows

## Overview

This directory contains GitHub Actions workflows for the Multi-Cloud Disaster Recovery System. The workflows automate testing, validation, and deployment across AWS, Azure, and GCP.

## Workflows

### 1. terraform-validation.yml
**Trigger**: Pull requests and pushes to main/develop branches (Terraform files)

**Purpose**: Validate Terraform configurations before deployment

**Jobs**:
- **terraform-fmt**: Check Terraform formatting
- **terraform-validate-aws**: Validate AWS Terraform configuration
- **terraform-validate-azure**: Validate Azure Terraform configuration
- **terraform-validate-gcp**: Validate GCP Terraform configuration
- **terraform-security-scan**: Run tfsec and Checkov security scans
- **terraform-cost-estimate**: Estimate infrastructure costs with Infracost
- **validation-summary**: Aggregate validation results

**Required Secrets**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AZURE_CREDENTIALS`
- `GCP_CREDENTIALS`
- `INFRACOST_API_KEY` (optional)

**Features**:
- Automatic PR comments with Terraform plans
- Security vulnerability scanning
- Cost estimation for infrastructure changes
- Parallel validation across all clouds

### 2. python-testing.yml
**Trigger**: Pull requests and pushes to main/develop branches (Python files)

**Purpose**: Test Python code quality and functionality

**Jobs**:
- **lint**: Run Black, isort, Flake8, Pylint, MyPy
- **unit-tests**: Run unit tests with coverage
- **property-based-tests**: Run Hypothesis property-based tests
- **security-scan**: Run Bandit and Safety checks
- **integration-tests**: Validate integration test syntax (dry run)
- **code-quality**: SonarCloud analysis
- **test-summary**: Aggregate test results

**Required Secrets**:
- `CODECOV_TOKEN` (optional)
- `SONAR_TOKEN` (optional)

**Features**:
- Code coverage reporting
- Security vulnerability scanning
- Automatic PR comments with test summary
- Property-based testing with Hypothesis

### 3. deployment.yml
**Trigger**: 
- Push to main branch
- Manual workflow dispatch

**Purpose**: Deploy infrastructure to cloud providers

**Jobs**:
- **pre-deployment-checks**: Validate deployment readiness
- **deploy-aws**: Deploy AWS infrastructure
- **deploy-azure**: Deploy Azure infrastructure
- **deploy-gcp**: Deploy GCP infrastructure
- **configure-dns**: Configure Route 53 DNS
- **post-deployment-tests**: Run smoke tests and verification
- **deployment-notification**: Send notifications
- **rollback**: Automatic rollback on failure (production only)

**Required Secrets**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AZURE_CREDENTIALS`
- `GCP_CREDENTIALS`
- `SLACK_WEBHOOK_URL` (optional)

**Features**:
- Selective deployment (all clouds or specific cloud)
- Environment-specific deployments (staging/production)
- Automatic smoke tests after deployment
- Slack notifications
- Automatic rollback on production failures
- GitHub deployment tracking

## Setup Instructions

### 1. Configure GitHub Secrets

Navigate to your repository settings → Secrets and variables → Actions, and add the following secrets:

#### AWS Credentials
```
AWS_ACCESS_KEY_ID: Your AWS access key
AWS_SECRET_ACCESS_KEY: Your AWS secret key
```

#### Azure Credentials
```
AZURE_CREDENTIALS: JSON object with Azure service principal credentials
```

Format:
```json
{
  "clientId": "your-client-id",
  "clientSecret": "your-client-secret",
  "subscriptionId": "your-subscription-id",
  "tenantId": "your-tenant-id"
}
```

To create Azure service principal:
```bash
az ad sp create-for-rbac --name "multicloud-dr-github" --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

#### GCP Credentials
```
GCP_CREDENTIALS: JSON service account key
```

To create GCP service account key:
```bash
gcloud iam service-accounts create multicloud-dr-github \
  --display-name="Multi-Cloud DR GitHub Actions"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:multicloud-dr-github@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/editor"

gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=multicloud-dr-github@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

#### Optional Secrets
```
INFRACOST_API_KEY: For cost estimation (get from https://www.infracost.io/)
CODECOV_TOKEN: For code coverage reporting (get from https://codecov.io/)
SONAR_TOKEN: For SonarCloud analysis (get from https://sonarcloud.io/)
SLACK_WEBHOOK_URL: For deployment notifications
```

### 2. Configure GitHub Environments

Create environments for deployment protection:

1. Go to Settings → Environments
2. Create environments:
   - `production-aws`
   - `production-azure`
   - `production-gcp`
   - `staging-aws`
   - `staging-azure`
   - `staging-gcp`

3. For production environments, configure:
   - Required reviewers (recommended)
   - Wait timer (optional)
   - Deployment branches (main only)

### 3. Enable GitHub Actions

1. Go to Settings → Actions → General
2. Set "Actions permissions" to "Allow all actions and reusable workflows"
3. Set "Workflow permissions" to "Read and write permissions"
4. Enable "Allow GitHub Actions to create and approve pull requests"

### 4. Configure Branch Protection

Protect the main branch:

1. Go to Settings → Branches
2. Add branch protection rule for `main`:
   - Require pull request reviews
   - Require status checks to pass:
     - `Terraform Format Check`
     - `Validate AWS Terraform`
     - `Validate Azure Terraform`
     - `Validate GCP Terraform`
     - `Unit Tests`
     - `Property-Based Tests`
   - Require branches to be up to date
   - Include administrators

## Usage

### Running Terraform Validation

Terraform validation runs automatically on pull requests. To manually trigger:

```bash
# Push changes to trigger validation
git push origin feature-branch

# Or use GitHub CLI
gh workflow run terraform-validation.yml
```

### Running Python Tests

Python tests run automatically on pull requests. To run locally:

```bash
# Install dependencies
pip install -r infrastructure/requirements.txt
pip install pytest pytest-cov hypothesis flake8 black

# Run tests
cd infrastructure
pytest tests/ -v --cov=.

# Run property-based tests
pytest tests/property/ -v

# Run linting
flake8 .
black --check .
```

### Deploying Infrastructure

#### Automatic Deployment (on merge to main)
```bash
# Merge PR to main branch
git checkout main
git merge feature-branch
git push origin main
```

#### Manual Deployment
1. Go to Actions tab in GitHub
2. Select "Deployment" workflow
3. Click "Run workflow"
4. Select:
   - Environment: staging or production
   - Cloud: all, aws, azure, or gcp
5. Click "Run workflow"

Or use GitHub CLI:
```bash
# Deploy all clouds to production
gh workflow run deployment.yml -f environment=production -f cloud=all

# Deploy only AWS to staging
gh workflow run deployment.yml -f environment=staging -f cloud=aws
```

### Monitoring Workflow Runs

#### Via GitHub UI
1. Go to Actions tab
2. Select workflow
3. View run details, logs, and artifacts

#### Via GitHub CLI
```bash
# List recent workflow runs
gh run list --workflow=deployment.yml

# View specific run
gh run view <run-id>

# Watch run in real-time
gh run watch <run-id>

# Download artifacts
gh run download <run-id>
```

## Workflow Outputs

### Terraform Validation
- PR comments with Terraform plans
- Security scan results (SARIF format)
- Cost estimates

### Python Testing
- Code coverage reports (HTML and XML)
- Test results
- Security scan reports
- SonarCloud analysis

### Deployment
- Terraform outputs (JSON)
- Smoke test results
- Deployment verification reports

## Troubleshooting

### Workflow Fails: "Resource not found"

**Problem**: Terraform can't find resources

**Solution**:
1. Verify Terraform backend is configured
2. Check AWS/Azure/GCP credentials are valid
3. Ensure resources exist in target environment

### Workflow Fails: "Permission denied"

**Problem**: Insufficient permissions

**Solution**:
1. Verify GitHub secrets are set correctly
2. Check IAM/RBAC permissions for service accounts
3. Ensure GitHub Actions has write permissions

### Workflow Fails: "Terraform state locked"

**Problem**: Another operation is in progress

**Solution**:
1. Wait for other operation to complete
2. Or manually unlock state:
```bash
terraform force-unlock <lock-id>
```

### Tests Fail Locally But Pass in CI

**Problem**: Environment differences

**Solution**:
1. Check Python version matches CI (3.9)
2. Install exact dependencies: `pip install -r requirements.txt`
3. Check environment variables

### Deployment Fails: "Timeout"

**Problem**: Deployment takes too long

**Solution**:
1. Increase timeout in workflow file
2. Check cloud provider status
3. Review Terraform logs for slow resources

## Best Practices

### Pull Requests
1. Always create PR for changes
2. Wait for all checks to pass
3. Review Terraform plans in PR comments
4. Get code review before merging

### Deployments
1. Deploy to staging first
2. Run integration tests manually
3. Monitor deployment progress
4. Verify health checks after deployment
5. Keep rollback plan ready

### Secrets Management
1. Rotate secrets regularly (every 90 days)
2. Use least privilege permissions
3. Never commit secrets to repository
4. Use environment-specific secrets

### Testing
1. Write tests for all new code
2. Maintain >80% code coverage
3. Run property-based tests locally
4. Fix linting issues before pushing

## Maintenance

### Updating Workflows

When updating workflows:
1. Test changes in feature branch
2. Review workflow syntax
3. Update this README if needed
4. Get review before merging

### Updating Dependencies

Update GitHub Actions:
```yaml
# Check for updates
uses: actions/checkout@v3  # Update to latest version
```

Update Python dependencies:
```bash
# Update requirements.txt
pip install --upgrade -r infrastructure/requirements.txt
pip freeze > infrastructure/requirements.txt
```

Update Terraform:
```yaml
# Update TF_VERSION in workflows
env:
  TF_VERSION: '1.6.0'  # Update to latest stable
```

### Monitoring Workflow Performance

Track metrics:
- Workflow run duration
- Success/failure rates
- Resource usage
- Cost per run

Optimize:
- Cache dependencies
- Parallelize jobs
- Skip unnecessary steps
- Use matrix builds

## Security Considerations

### Secrets
- Never log secrets
- Use GitHub secrets, not environment variables
- Rotate regularly
- Audit access

### Permissions
- Use least privilege
- Separate staging and production
- Require reviews for production
- Enable branch protection

### Dependencies
- Keep actions up to date
- Review security advisories
- Use pinned versions
- Scan for vulnerabilities

## Support

For issues with CI/CD workflows:
1. Check workflow logs in GitHub Actions
2. Review this README
3. Consult GitHub Actions documentation
4. Contact DevOps team

## Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Terraform Documentation](https://www.terraform.io/docs)
- [Deployment Guide](../../infrastructure/docs/DEPLOYMENT_GUIDE.md)
- [Architecture Documentation](../../infrastructure/docs/ARCHITECTURE.md)

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2024-01-15 | 1.0 | DevOps Team | Initial version |
