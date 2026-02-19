#!/usr/bin/env python3
"""
IAM Policy Audit Script

This script audits IAM policies across AWS, Azure, and GCP to ensure
least privilege principles are followed.

Features:
- Review IAM role permissions on AWS
- Review RBAC assignments on Azure
- Review IAM bindings on GCP
- Identify overly permissive policies
- Generate audit reports
- Recommend permission reductions
"""

import sys
import logging
import json
from typing import Dict, List, Tuple
from datetime import datetime

try:
    import boto3
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.authorization import AuthorizationManagementClient
    from google.cloud import iam_admin_v1
    from google.cloud import resourcemanager_v3
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install boto3 azure-identity azure-mgmt-authorization google-cloud-iam google-cloud-resource-manager")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IAMAuditor:
    """Audits IAM policies across cloud providers"""
    
    def __init__(self, config: Dict):
        """Initialize IAM auditor"""
        self.config = config
        self.audit_results = {
            'aws': [],
            'azure': [],
            'gcp': [],
            'summary': {}
        }
    
    def audit_aws_policies(self) -> List[Dict]:
        """Audit AWS IAM policies"""
        logger.info("Auditing AWS IAM policies...")
        findings = []
        
        try:
            iam_client = boto3.client('iam', region_name=self.config.get('aws_region', 'us-east-1'))
            
            # Get all roles
            paginator = iam_client.get_paginator('list_roles')
            for page in paginator.paginate():
                for role in page['Roles']:
                    role_name = role['RoleName']
                    
                    # Skip AWS service roles
                    if role_name.startswith('AWS'):
                        continue
                    
                    # Get attached policies
                    attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
                    
                    for policy in attached_policies['AttachedPolicies']:
                        policy_arn = policy['PolicyArn']
                        
                        # Get policy details
                        policy_details = iam_client.get_policy(PolicyArn=policy_arn)
                        policy_version = iam_client.get_policy_version(
                            PolicyArn=policy_arn,
                            VersionId=policy_details['Policy']['DefaultVersionId']
                        )
                        
                        # Analyze policy document
                        policy_doc = policy_version['PolicyVersion']['Document']
                        issues = self._analyze_aws_policy(policy_doc, role_name)
                        
                        if issues:
                            findings.append({
                                'role': role_name,
                                'policy': policy['PolicyName'],
                                'policy_arn': policy_arn,
                                'issues': issues
                            })
            
            logger.info(f"Found {len(findings)} AWS IAM issues")
            return findings
            
        except Exception as e:
            logger.error(f"Error auditing AWS policies: {e}")
            return []
    
    def _analyze_aws_policy(self, policy_doc: Dict, role_name: str) -> List[str]:
        """Analyze AWS policy document for issues"""
        issues = []
        
        for statement in policy_doc.get('Statement', []):
            # Check for overly broad permissions
            actions = statement.get('Action', [])
            if isinstance(actions, str):
                actions = [actions]
            
            for action in actions:
                # Check for wildcard actions
                if action == '*' or action.endswith(':*'):
                    issues.append(f"Overly broad action: {action}")
                
                # Check for dangerous permissions
                dangerous_actions = [
                    'iam:*',
                    'iam:CreateUser',
                    'iam:CreateRole',
                    'iam:PutRolePolicy',
                    'iam:AttachRolePolicy',
                    's3:*',
                    'ec2:*'
                ]
                
                if action in dangerous_actions:
                    issues.append(f"Potentially dangerous action: {action}")
            
            # Check for wildcard resources
            resources = statement.get('Resource', [])
            if isinstance(resources, str):
                resources = [resources]
            
            for resource in resources:
                if resource == '*':
                    issues.append("Wildcard resource (*) - should be more specific")
        
        return issues
    
    def audit_azure_policies(self) -> List[Dict]:
        """Audit Azure RBAC assignments"""
        logger.info("Auditing Azure RBAC assignments...")
        findings = []
        
        try:
            if 'azure_subscription_id' not in self.config:
                logger.warning("Azure subscription ID not configured")
                return []
            
            credential = DefaultAzureCredential()
            auth_client = AuthorizationManagementClient(
                credential,
                self.config['azure_subscription_id']
            )
            
            # Get all role assignments
            role_assignments = auth_client.role_assignments.list()
            
            for assignment in role_assignments:
                # Get role definition
                role_def = auth_client.role_definitions.get_by_id(assignment.role_definition_id)
                
                # Check for overly permissive roles
                issues = self._analyze_azure_role(role_def)
                
                if issues:
                    findings.append({
                        'principal_id': assignment.principal_id,
                        'role': role_def.role_name,
                        'scope': assignment.scope,
                        'issues': issues
                    })
            
            logger.info(f"Found {len(findings)} Azure RBAC issues")
            return findings
            
        except Exception as e:
            logger.error(f"Error auditing Azure policies: {e}")
            return []
    
    def _analyze_azure_role(self, role_def) -> List[str]:
        """Analyze Azure role definition for issues"""
        issues = []
        
        # Check for built-in overly permissive roles
        overly_permissive_roles = [
            'Owner',
            'Contributor',
            'User Access Administrator'
        ]
        
        if role_def.role_name in overly_permissive_roles:
            issues.append(f"Overly permissive built-in role: {role_def.role_name}")
        
        # Check permissions
        for permission in role_def.permissions:
            for action in permission.actions:
                if action == '*':
                    issues.append("Wildcard action (*) - should be more specific")
                
                # Check for dangerous permissions
                if 'Microsoft.Authorization' in action:
                    issues.append(f"Authorization management permission: {action}")
        
        return issues
    
    def audit_gcp_policies(self) -> List[Dict]:
        """Audit GCP IAM bindings"""
        logger.info("Auditing GCP IAM bindings...")
        findings = []
        
        try:
            if 'gcp_project_id' not in self.config:
                logger.warning("GCP project ID not configured")
                return []
            
            # Get project IAM policy
            client = resourcemanager_v3.ProjectsClient()
            project_name = f"projects/{self.config['gcp_project_id']}"
            
            policy = client.get_iam_policy(resource=project_name)
            
            for binding in policy.bindings:
                issues = self._analyze_gcp_role(binding.role)
                
                if issues:
                    findings.append({
                        'role': binding.role,
                        'members': list(binding.members),
                        'issues': issues
                    })
            
            logger.info(f"Found {len(findings)} GCP IAM issues")
            return findings
            
        except Exception as e:
            logger.error(f"Error auditing GCP policies: {e}")
            return []
    
    def _analyze_gcp_role(self, role: str) -> List[str]:
        """Analyze GCP role for issues"""
        issues = []
        
        # Check for overly permissive roles
        overly_permissive_roles = [
            'roles/owner',
            'roles/editor',
            'roles/iam.securityAdmin'
        ]
        
        if role in overly_permissive_roles:
            issues.append(f"Overly permissive role: {role}")
        
        return issues
    
    def generate_report(self) -> str:
        """Generate audit report"""
        logger.info("Generating audit report...")
        
        # Run audits
        self.audit_results['aws'] = self.audit_aws_policies()
        self.audit_results['azure'] = self.audit_azure_policies()
        self.audit_results['gcp'] = self.audit_gcp_policies()
        
        # Generate summary
        self.audit_results['summary'] = {
            'total_issues': (
                len(self.audit_results['aws']) +
                len(self.audit_results['azure']) +
                len(self.audit_results['gcp'])
            ),
            'aws_issues': len(self.audit_results['aws']),
            'azure_issues': len(self.audit_results['azure']),
            'gcp_issues': len(self.audit_results['gcp']),
            'timestamp': datetime.now().isoformat()
        }
        
        # Format report
        report = f"""
IAM Policy Audit Report
Generated: {self.audit_results['summary']['timestamp']}

Summary:
--------
Total Issues: {self.audit_results['summary']['total_issues']}
AWS Issues: {self.audit_results['summary']['aws_issues']}
Azure Issues: {self.audit_results['summary']['azure_issues']}
GCP Issues: {self.audit_results['summary']['gcp_issues']}

AWS Findings:
-------------
"""
        
        for finding in self.audit_results['aws']:
            report += f"\nRole: {finding['role']}\n"
            report += f"Policy: {finding['policy']}\n"
            report += "Issues:\n"
            for issue in finding['issues']:
                report += f"  - {issue}\n"
        
        report += "\nAzure Findings:\n---------------\n"
        
        for finding in self.audit_results['azure']:
            report += f"\nPrincipal: {finding['principal_id']}\n"
            report += f"Role: {finding['role']}\n"
            report += f"Scope: {finding['scope']}\n"
            report += "Issues:\n"
            for issue in finding['issues']:
                report += f"  - {issue}\n"
        
        report += "\nGCP Findings:\n-------------\n"
        
        for finding in self.audit_results['gcp']:
            report += f"\nRole: {finding['role']}\n"
            report += f"Members: {', '.join(finding['members'])}\n"
            report += "Issues:\n"
            for issue in finding['issues']:
                report += f"  - {issue}\n"
        
        report += "\nRecommendations:\n----------------\n"
        report += "1. Replace wildcard permissions with specific resource ARNs\n"
        report += "2. Remove unused permissions from roles\n"
        report += "3. Use managed identities instead of access keys\n"
        report += "4. Implement regular permission reviews\n"
        report += "5. Enable CloudTrail/Activity Log for IAM changes\n"
        
        return report
    
    def save_report(self, filename: str):
        """Save audit report to file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            f.write(report)
        
        # Also save JSON version
        json_filename = filename.replace('.txt', '.json')
        with open(json_filename, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        logger.info(f"Report saved to {filename} and {json_filename}")


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IAM Policy Audit Script')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--output', default='iam_audit_report.txt', help='Output report filename')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize auditor
    auditor = IAMAuditor(config)
    
    # Generate and save report
    auditor.save_report(args.output)
    
    # Print summary
    print(f"\nAudit complete!")
    print(f"Total issues found: {auditor.audit_results['summary']['total_issues']}")
    print(f"Report saved to: {args.output}")


if __name__ == '__main__':
    main()
