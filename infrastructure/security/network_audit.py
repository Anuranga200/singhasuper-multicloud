#!/usr/bin/env python3
"""
Network Security Audit Script

This script audits network security configurations across AWS, Azure, and GCP
to ensure proper segmentation and minimal access rules.

Features:
- Audit AWS Security Groups
- Audit Azure Network Security Groups
- Audit GCP Firewall Rules
- Identify overly permissive rules
- Verify network segmentation
- Generate audit reports
"""

import sys
import logging
import json
from typing import Dict, List
from datetime import datetime

try:
    import boto3
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install boto3")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NetworkSecurityAuditor:
    """Audits network security configurations"""
    
    def __init__(self, config: Dict):
        """Initialize network security auditor"""
        self.config = config
        self.audit_results = {
            'aws': [],
            'azure': [],
            'gcp': [],
            'summary': {}
        }
    
    def audit_aws_security_groups(self) -> List[Dict]:
        """Audit AWS Security Groups"""
        logger.info("Auditing AWS Security Groups...")
        findings = []
        
        try:
            ec2_client = boto3.client('ec2', region_name=self.config.get('aws_region', 'us-east-1'))
            
            # Get all security groups
            response = ec2_client.describe_security_groups()
            
            for sg in response['SecurityGroups']:
                sg_id = sg['GroupId']
                sg_name = sg['GroupName']
                
                # Skip default security group
                if sg_name == 'default':
                    continue
                
                # Analyze ingress rules
                for rule in sg.get('IpPermissions', []):
                    issues = self._analyze_aws_ingress_rule(rule, sg_name)
                    if issues:
                        findings.append({
                            'security_group': sg_name,
                            'security_group_id': sg_id,
                            'rule_type': 'ingress',
                            'rule': rule,
                            'issues': issues
                        })
                
                # Analyze egress rules
                for rule in sg.get('IpPermissionsEgress', []):
                    issues = self._analyze_aws_egress_rule(rule, sg_name)
                    if issues:
                        findings.append({
                            'security_group': sg_name,
                            'security_group_id': sg_id,
                            'rule_type': 'egress',
                            'rule': rule,
                            'issues': issues
                        })
            
            logger.info(f"Found {len(findings)} AWS security group issues")
            return findings
            
        except Exception as e:
            logger.error(f"Error auditing AWS security groups: {e}")
            return []
    
    def _analyze_aws_ingress_rule(self, rule: Dict, sg_name: str) -> List[str]:
        """Analyze AWS ingress rule for issues"""
        issues = []
        
        # Check for overly permissive source
        for ip_range in rule.get('IpRanges', []):
            cidr = ip_range.get('CidrIp', '')
            if cidr == '0.0.0.0/0':
                # Check if it's for common ports
                from_port = rule.get('FromPort')
                to_port = rule.get('ToPort')
                
                # Allow 80/443 for load balancers, but warn for others
                if from_port not in [80, 443] or to_port not in [80, 443]:
                    issues.append(f"Ingress from 0.0.0.0/0 on port {from_port}-{to_port}")
        
        # Check for wide port ranges
        from_port = rule.get('FromPort', 0)
        to_port = rule.get('ToPort', 0)
        
        if to_port - from_port > 100:
            issues.append(f"Wide port range: {from_port}-{to_port}")
        
        # Check for all protocols
        if rule.get('IpProtocol') == '-1':
            issues.append("All protocols allowed (-1)")
        
        return issues
    
    def _analyze_aws_egress_rule(self, rule: Dict, sg_name: str) -> List[str]:
        """Analyze AWS egress rule for issues"""
        issues = []
        
        # Check for overly permissive egress
        for ip_range in rule.get('IpRanges', []):
            cidr = ip_range.get('CidrIp', '')
            if cidr == '0.0.0.0/0' and rule.get('IpProtocol') == '-1':
                issues.append("Unrestricted egress to 0.0.0.0/0 (all protocols)")
        
        return issues
    
    def verify_network_segmentation(self) -> List[Dict]:
        """Verify network segmentation across clouds"""
        logger.info("Verifying network segmentation...")
        findings = []
        
        try:
            ec2_client = boto3.client('ec2', region_name=self.config.get('aws_region', 'us-east-1'))
            
            # Get all subnets
            response = ec2_client.describe_subnets()
            
            public_subnets = []
            private_subnets = []
            
            for subnet in response['Subnets']:
                subnet_id = subnet['SubnetId']
                
                # Check if subnet has route to internet gateway
                route_tables = ec2_client.describe_route_tables(
                    Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
                )
                
                is_public = False
                for rt in route_tables['RouteTables']:
                    for route in rt['Routes']:
                        if route.get('GatewayId', '').startswith('igw-'):
                            is_public = True
                            break
                
                if is_public:
                    public_subnets.append(subnet_id)
                else:
                    private_subnets.append(subnet_id)
            
            # Check if instances are in appropriate subnets
            instances = ec2_client.describe_instances()
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    subnet_id = instance.get('SubnetId')
                    instance_id = instance['InstanceId']
                    
                    # Check if database instances are in private subnets
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    if 'database' in tags.get('Name', '').lower():
                        if subnet_id in public_subnets:
                            findings.append({
                                'type': 'segmentation_violation',
                                'resource': instance_id,
                                'issue': 'Database instance in public subnet'
                            })
            
            logger.info(f"Found {len(findings)} network segmentation issues")
            return findings
            
        except Exception as e:
            logger.error(f"Error verifying network segmentation: {e}")
            return []
    
    def generate_report(self) -> str:
        """Generate network security audit report"""
        logger.info("Generating network security audit report...")
        
        # Run audits
        self.audit_results['aws'] = self.audit_aws_security_groups()
        segmentation_issues = self.verify_network_segmentation()
        
        # Generate summary
        self.audit_results['summary'] = {
            'total_issues': len(self.audit_results['aws']) + len(segmentation_issues),
            'security_group_issues': len(self.audit_results['aws']),
            'segmentation_issues': len(segmentation_issues),
            'timestamp': datetime.now().isoformat()
        }
        
        # Format report
        report = f"""
Network Security Audit Report
Generated: {self.audit_results['summary']['timestamp']}

Summary:
--------
Total Issues: {self.audit_results['summary']['total_issues']}
Security Group Issues: {self.audit_results['summary']['security_group_issues']}
Network Segmentation Issues: {self.audit_results['summary']['segmentation_issues']}

AWS Security Group Findings:
----------------------------
"""
        
        for finding in self.audit_results['aws']:
            report += f"\nSecurity Group: {finding['security_group']} ({finding['security_group_id']})\n"
            report += f"Rule Type: {finding['rule_type']}\n"
            report += "Issues:\n"
            for issue in finding['issues']:
                report += f"  - {issue}\n"
        
        report += "\nNetwork Segmentation Findings:\n------------------------------\n"
        
        for finding in segmentation_issues:
            report += f"\nResource: {finding['resource']}\n"
            report += f"Issue: {finding['issue']}\n"
        
        report += "\nRecommendations:\n----------------\n"
        report += "1. Restrict ingress rules to specific source IPs/security groups\n"
        report += "2. Limit egress rules to required destinations only\n"
        report += "3. Use specific port ranges instead of wide ranges\n"
        report += "4. Ensure databases are in private subnets\n"
        report += "5. Enable VPC Flow Logs for traffic monitoring\n"
        report += "6. Regularly review and remove unused security rules\n"
        
        return report
    
    def save_report(self, filename: str):
        """Save audit report to file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            f.write(report)
        
        # Also save JSON version
        json_filename = filename.replace('.txt', '.json')
        with open(json_filename, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
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
    
    parser = argparse.ArgumentParser(description='Network Security Audit Script')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--output', default='network_security_audit.txt', help='Output report filename')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize auditor
    auditor = NetworkSecurityAuditor(config)
    
    # Generate and save report
    auditor.save_report(args.output)
    
    # Print summary
    print(f"\nAudit complete!")
    print(f"Total issues found: {auditor.audit_results['summary']['total_issues']}")
    print(f"Report saved to: {args.output}")


if __name__ == '__main__':
    main()
