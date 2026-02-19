#!/usr/bin/env python3
"""
Deployment Verification Script
Validates that all infrastructure components are deployed correctly across AWS, Azure, and GCP
"""

import sys
import os
from typing import Dict, List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_section(text: str):
    print(f"\n{YELLOW}▶ {text}{RESET}")


def print_success(text: str):
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text: str):
    print(f"{RED}✗{RESET} {text}")


def print_warning(text: str):
    print(f"{YELLOW}⚠{RESET} {text}")


def verify_aws_deployment() -> Tuple[bool, List[str]]:
    """Verify AWS infrastructure deployment"""
    print_section("Verifying AWS Infrastructure")
    
    errors = []
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Check AWS credentials
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print_success(f"AWS credentials valid (Account: {identity['Account']})")
        except NoCredentialsError:
            errors.append("AWS credentials not configured")
            print_error("AWS credentials not configured")
            return False, errors
        
        # Import validator
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'property'))
        from test_aws_deployment import AWSDeploymentValidator
        
        validator = AWSDeploymentValidator()
        project_name = 'singha-loyalty'
        environment = 'prod'
        
        results = validator.validate_deployment(project_name, environment)
        
        for component, exists in results.items():
            if exists:
                print_success(f"{component.replace('_', ' ').title()}")
            else:
                error_msg = f"AWS {component.replace('_', ' ')} not found"
                errors.append(error_msg)
                print_error(error_msg)
        
        return len(errors) == 0, errors
        
    except ImportError as e:
        error_msg = f"Missing Python dependency: {e}"
        errors.append(error_msg)
        print_error(error_msg)
        return False, errors
    except Exception as e:
        error_msg = f"AWS verification failed: {e}"
        errors.append(error_msg)
        print_error(error_msg)
        return False, errors


def verify_azure_deployment() -> Tuple[bool, List[str]]:
    """Verify Azure infrastructure deployment"""
    print_section("Verifying Azure Infrastructure")
    
    errors = []
    
    try:
        from azure.identity import DefaultAzureCredential
        from azure.core.exceptions import ClientAuthenticationError
        
        # Check Azure credentials
        try:
            credential = DefaultAzureCredential()
            # Test credential by attempting to get a token
            credential.get_token("https://management.azure.com/.default")
            print_success("Azure credentials valid")
        except ClientAuthenticationError:
            errors.append("Azure credentials not configured")
            print_error("Azure credentials not configured")
            return False, errors
        
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if not subscription_id:
            errors.append("AZURE_SUBSCRIPTION_ID environment variable not set")
            print_error("AZURE_SUBSCRIPTION_ID not set")
            return False, errors
        
        # Import validator
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'property'))
        from test_azure_deployment import AzureDeploymentValidator
        
        validator = AzureDeploymentValidator(subscription_id)
        project_name = 'singha-loyalty'
        environment = 'prod'
        
        results = validator.validate_deployment(project_name, environment)
        
        for component, exists in results.items():
            if exists:
                print_success(f"{component.replace('_', ' ').title()}")
            else:
                error_msg = f"Azure {component.replace('_', ' ')} not found"
                errors.append(error_msg)
                print_error(error_msg)
        
        return len(errors) == 0, errors
        
    except ImportError as e:
        error_msg = f"Missing Python dependency: {e}"
        errors.append(error_msg)
        print_error(error_msg)
        return False, errors
    except Exception as e:
        error_msg = f"Azure verification failed: {e}"
        errors.append(error_msg)
        print_error(error_msg)
        return False, errors


def verify_gcp_deployment() -> Tuple[bool, List[str]]:
    """Verify GCP infrastructure deployment"""
    print_section("Verifying GCP Infrastructure")
    
    errors = []
    
    try:
        from google.auth import default
        from google.auth.exceptions import DefaultCredentialsError
        
        # Check GCP credentials
        try:
            credentials, project_id = default()
            print_success(f"GCP credentials valid (Project: {project_id})")
        except DefaultCredentialsError:
            errors.append("GCP credentials not configured")
            print_error("GCP credentials not configured")
            return False, errors
        
        project_id = os.getenv('GCP_PROJECT_ID', project_id)
        if not project_id:
            errors.append("GCP_PROJECT_ID not set")
            print_error("GCP_PROJECT_ID not set")
            return False, errors
        
        # Import validator
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'property'))
        from test_gcp_deployment import GCPDeploymentValidator
        
        validator = GCPDeploymentValidator(project_id)
        project_name = 'singha-loyalty'
        environment = 'prod'
        
        results = validator.validate_deployment(project_name, environment, 'us-central1')
        
        for component, exists in results.items():
            if exists:
                print_success(f"{component.replace('_', ' ').title()}")
            else:
                error_msg = f"GCP {component.replace('_', ' ')} not found"
                errors.append(error_msg)
                print_error(error_msg)
        
        return len(errors) == 0, errors
        
    except ImportError as e:
        error_msg = f"Missing Python dependency: {e}"
        errors.append(error_msg)
        print_error(error_msg)
        return False, errors
    except Exception as e:
        error_msg = f"GCP verification failed: {e}"
        errors.append(error_msg)
        print_error(error_msg)
        return False, errors


def run_property_tests() -> Tuple[bool, List[str]]:
    """Run property-based tests"""
    print_section("Running Property-Based Tests")
    
    errors = []
    
    try:
        import pytest
        
        test_dir = os.path.join(os.path.dirname(__file__), 'property')
        
        # Run tests with pytest
        result = pytest.main([
            test_dir,
            '-v',
            '--tb=short',
            '--maxfail=1'
        ])
        
        if result == 0:
            print_success("All property tests passed")
            return True, []
        else:
            error_msg = "Some property tests failed"
            errors.append(error_msg)
            print_error(error_msg)
            return False, errors
            
    except ImportError:
        error_msg = "pytest not installed"
        errors.append(error_msg)
        print_error(error_msg)
        return False, errors
    except Exception as e:
        error_msg = f"Test execution failed: {e}"
        errors.append(error_msg)
        print_error(error_msg)
        return False, errors


def main():
    """Main verification workflow"""
    print_header("Multi-Cloud DR System - Deployment Verification")
    
    all_errors = []
    results = {}
    
    # Verify each cloud
    aws_ok, aws_errors = verify_aws_deployment()
    results['AWS'] = aws_ok
    all_errors.extend(aws_errors)
    
    azure_ok, azure_errors = verify_azure_deployment()
    results['Azure'] = azure_ok
    all_errors.extend(azure_errors)
    
    gcp_ok, gcp_errors = verify_gcp_deployment()
    results['GCP'] = gcp_ok
    all_errors.extend(gcp_errors)
    
    # Run property tests if deployments exist
    if any(results.values()):
        tests_ok, test_errors = run_property_tests()
        results['Tests'] = tests_ok
        all_errors.extend(test_errors)
    
    # Print summary
    print_header("Verification Summary")
    
    for cloud, status in results.items():
        if status:
            print_success(f"{cloud}: All checks passed")
        else:
            print_error(f"{cloud}: Issues found")
    
    if all_errors:
        print(f"\n{RED}Issues Found:{RESET}")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
    
    # Exit with appropriate code
    if all(results.values()):
        print(f"\n{GREEN}✓ All verifications passed!{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}✗ Verification failed. Please address the issues above.{RESET}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
