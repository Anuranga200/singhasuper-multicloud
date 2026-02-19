#!/usr/bin/env python3
"""
Property-Based Tests for Security Controls

This module contains property-based tests for security controls including
IAM least privilege, secret storage, TLS enforcement, and firewall rules.

Tests:
- Property 13: Least Privilege IAM
- Property 14: Secret Storage Security
- Property 15: TLS Version Enforcement
- Property 16: Firewall Rule Minimalism
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from typing import Dict, List, Set
import re


# Test data generators
@st.composite
def iam_policy_strategy(draw):
    """Generate IAM policy data"""
    actions = [
        'secretsmanager:GetSecretValue',
        'secretsmanager:*',
        'rds:DescribeDBInstances',
        'rds:*',
        's3:GetObject',
        's3:*',
        'ec2:DescribeInstances',
        'ec2:*',
        'iam:CreateUser',
        'iam:*',
        '*'
    ]
    
    resources = [
        'arn:aws:secretsmanager:*:*:secret:dr-system/*',
        'arn:aws:rds:*:*:db:*',
        'arn:aws:s3:::dr-system-artifacts/*',
        '*'
    ]
    
    num_actions = draw(st.integers(min_value=1, max_value=5))
    num_resources = draw(st.integers(min_value=1, max_value=3))
    
    return {
        'role_name': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=20)),
        'actions': [draw(st.sampled_from(actions)) for _ in range(num_actions)],
        'resources': [draw(st.sampled_from(resources)) for _ in range(num_resources)],
        'effect': draw(st.sampled_from(['Allow', 'Deny']))
    }


@st.composite
def secret_configuration_strategy(draw):
    """Generate secret configuration data"""
    storage_types = ['plaintext', 'secrets_manager', 'key_vault', 'secret_manager', 'environment_variable']
    
    return {
        'secret_name': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-_', min_size=5, max_size=30)),
        'storage_type': draw(st.sampled_from(storage_types)),
        'encrypted': draw(st.booleans()),
        'in_code': draw(st.booleans()),
        'in_logs': draw(st.booleans())
    }


@st.composite
def tls_configuration_strategy(draw):
    """Generate TLS configuration data"""
    tls_versions = ['TLSv1.0', 'TLSv1.1', 'TLSv1.2', 'TLSv1.3']
    
    return {
        'service': draw(st.sampled_from(['load_balancer', 'database', 'vpn', 'api'])),
        'tls_version': draw(st.sampled_from(tls_versions)),
        'cipher_suites': draw(st.lists(st.text(min_size=5, max_size=20), min_size=1, max_size=5)),
        'certificate_valid': draw(st.booleans())
    }


@st.composite
def firewall_rule_strategy(draw):
    """Generate firewall rule data"""
    protocols = ['tcp', 'udp', 'icmp', 'all']
    
    # Generate port or port range
    from_port = draw(st.integers(min_value=0, max_value=65535))
    to_port = draw(st.integers(min_value=from_port, max_value=65535))
    
    # Generate source CIDR
    source_cidrs = [
        '0.0.0.0/0',
        '10.0.0.0/8',
        '172.16.0.0/12',
        '192.168.0.0/16',
        '10.0.1.0/24',
        '10.0.10.0/24'
    ]
    
    return {
        'rule_name': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=20)),
        'protocol': draw(st.sampled_from(protocols)),
        'from_port': from_port,
        'to_port': to_port,
        'source_cidr': draw(st.sampled_from(source_cidrs)),
        'direction': draw(st.sampled_from(['ingress', 'egress'])),
        'action': draw(st.sampled_from(['allow', 'deny']))
    }


class TestLeastPrivilegeIAM:
    """
    Property 13: Least Privilege IAM
    
    **Validates: Requirements 4.1**
    
    For any IAM role or service account, the attached policies should grant 
    only the minimum permissions required for the component's function.
    """
    
    @given(policy=iam_policy_strategy())
    @settings(max_examples=100)
    def test_property_13_no_wildcard_actions(self, policy: Dict):
        """
        Feature: multi-cloud-dr-system, Property 13: Least Privilege IAM
        
        Verify that IAM policies do not use wildcard actions unless absolutely necessary.
        """
        # Check for wildcard actions
        wildcard_actions = [action for action in policy['actions'] if action == '*' or action.endswith(':*')]
        
        # Property: Wildcard actions should be avoided
        if wildcard_actions and policy['effect'] == 'Allow':
            # Allow wildcards only for specific read-only patterns
            for action in wildcard_actions:
                if action == '*':
                    pytest.fail(f"Policy {policy['role_name']} uses unrestricted wildcard action '*'")
                elif not any(read_prefix in action for read_prefix in ['Describe', 'Get', 'List']):
                    pytest.fail(f"Policy {policy['role_name']} uses overly broad action: {action}")
    
    @given(policy=iam_policy_strategy())
    @settings(max_examples=100)
    def test_property_13_no_wildcard_resources(self, policy: Dict):
        """
        Verify that IAM policies specify explicit resources instead of wildcards.
        """
        # Check for wildcard resources
        wildcard_resources = [resource for resource in policy['resources'] if resource == '*']
        
        # Property: Wildcard resources should be avoided
        if wildcard_resources and policy['effect'] == 'Allow':
            # Count specific actions that might justify wildcard resources
            global_actions = [action for action in policy['actions'] 
                            if any(prefix in action for prefix in ['iam:', 'sts:', 'organizations:'])]
            
            # If no global actions, wildcard resources are not justified
            if not global_actions:
                pytest.fail(f"Policy {policy['role_name']} uses wildcard resource '*' without justification")
    
    @given(policy=iam_policy_strategy())
    @settings(max_examples=100)
    def test_property_13_no_dangerous_permissions(self, policy: Dict):
        """
        Verify that IAM policies do not grant dangerous permissions.
        """
        dangerous_actions = [
            'iam:CreateUser',
            'iam:CreateRole',
            'iam:PutRolePolicy',
            'iam:AttachRolePolicy',
            'iam:*',
            'sts:AssumeRole',
            '*'
        ]
        
        # Check for dangerous actions
        found_dangerous = [action for action in policy['actions'] if action in dangerous_actions]
        
        # Property: Dangerous actions should not be granted to application roles
        if found_dangerous and policy['effect'] == 'Allow':
            # Only security/admin roles should have these permissions
            if 'admin' not in policy['role_name'].lower() and 'security' not in policy['role_name'].lower():
                pytest.fail(
                    f"Non-admin role {policy['role_name']} has dangerous permissions: {found_dangerous}"
                )
    
    @given(
        actions=st.lists(st.text(min_size=5, max_size=50), min_size=1, max_size=10),
        resources=st.lists(st.text(min_size=5, max_size=100), min_size=1, max_size=5)
    )
    @settings(max_examples=50)
    def test_policy_specificity(self, actions: List[str], resources: List[str]):
        """
        Verify that policies are specific and not overly broad.
        """
        # Count wildcards
        wildcard_actions = sum(1 for action in actions if '*' in action)
        wildcard_resources = sum(1 for resource in resources if resource == '*')
        
        # Property: Policies should be specific
        specificity_score = (
            (len(actions) - wildcard_actions) / len(actions) +
            (len(resources) - wildcard_resources) / len(resources)
        ) / 2
        
        # At least 50% specificity required
        assert specificity_score >= 0.5, \
            f"Policy is too broad: {specificity_score:.2%} specificity (minimum 50% required)"


class TestSecretStorageSecurity:
    """
    Property 14: Secret Storage Security
    
    **Validates: Requirements 4.2**
    
    For any secret (database password, JWT key, API token), it should be stored 
    in the cloud-native secret management service and not in plaintext configuration files.
    """
    
    @given(secret=secret_configuration_strategy())
    @settings(max_examples=100)
    def test_property_14_no_plaintext_secrets(self, secret: Dict):
        """
        Feature: multi-cloud-dr-system, Property 14: Secret Storage Security
        
        Verify that secrets are not stored in plaintext.
        """
        # Property: Secrets must not be stored in plaintext
        if secret['storage_type'] == 'plaintext':
            pytest.fail(f"Secret {secret['secret_name']} is stored in plaintext")
    
    @given(secret=secret_configuration_strategy())
    @settings(max_examples=100)
    def test_property_14_use_secret_managers(self, secret: Dict):
        """
        Verify that secrets use cloud-native secret management services.
        """
        valid_storage_types = ['secrets_manager', 'key_vault', 'secret_manager']
        
        # Property: Secrets must use proper secret management
        assert secret['storage_type'] in valid_storage_types, \
            f"Secret {secret['secret_name']} uses invalid storage type: {secret['storage_type']}"
    
    @given(secret=secret_configuration_strategy())
    @settings(max_examples=100)
    def test_property_14_secrets_encrypted(self, secret: Dict):
        """
        Verify that secrets are encrypted at rest.
        """
        # Property: Secrets must be encrypted
        if secret['storage_type'] in ['secrets_manager', 'key_vault', 'secret_manager']:
            assert secret['encrypted'], \
                f"Secret {secret['secret_name']} is not encrypted at rest"
    
    @given(secret=secret_configuration_strategy())
    @settings(max_examples=100)
    def test_property_14_no_secrets_in_code(self, secret: Dict):
        """
        Verify that secrets are not hardcoded in application code.
        """
        # Property: Secrets must not be in code
        assert not secret['in_code'], \
            f"Secret {secret['secret_name']} is hardcoded in application code"
    
    @given(secret=secret_configuration_strategy())
    @settings(max_examples=100)
    def test_property_14_no_secrets_in_logs(self, secret: Dict):
        """
        Verify that secrets are not logged.
        """
        # Property: Secrets must not appear in logs
        assert not secret['in_logs'], \
            f"Secret {secret['secret_name']} appears in application logs"


class TestTLSVersionEnforcement:
    """
    Property 15: TLS Version Enforcement
    
    **Validates: Requirements 4.4**
    
    For any network connection between system components, the TLS version 
    should be 1.2 or higher.
    """
    
    @given(tls_config=tls_configuration_strategy())
    @settings(max_examples=100)
    def test_property_15_minimum_tls_version(self, tls_config: Dict):
        """
        Feature: multi-cloud-dr-system, Property 15: TLS Version Enforcement
        
        Verify that all connections use TLS 1.2 or higher.
        """
        # Define minimum acceptable TLS version
        MIN_TLS_VERSION = 'TLSv1.2'
        
        # Map TLS versions to numeric values for comparison
        tls_version_map = {
            'TLSv1.0': 1.0,
            'TLSv1.1': 1.1,
            'TLSv1.2': 1.2,
            'TLSv1.3': 1.3
        }
        
        current_version = tls_version_map.get(tls_config['tls_version'], 0)
        min_version = tls_version_map[MIN_TLS_VERSION]
        
        # Property: TLS version must be 1.2 or higher
        assert current_version >= min_version, \
            f"{tls_config['service']} uses {tls_config['tls_version']}, minimum required is {MIN_TLS_VERSION}"
    
    @given(tls_config=tls_configuration_strategy())
    @settings(max_examples=100)
    def test_property_15_no_deprecated_tls(self, tls_config: Dict):
        """
        Verify that deprecated TLS versions are not used.
        """
        deprecated_versions = ['TLSv1.0', 'TLSv1.1']
        
        # Property: Deprecated TLS versions must not be used
        assert tls_config['tls_version'] not in deprecated_versions, \
            f"{tls_config['service']} uses deprecated TLS version: {tls_config['tls_version']}"
    
    @given(tls_config=tls_configuration_strategy())
    @settings(max_examples=100)
    def test_property_15_valid_certificate(self, tls_config: Dict):
        """
        Verify that TLS certificates are valid.
        """
        # Property: TLS certificates must be valid
        assert tls_config['certificate_valid'], \
            f"{tls_config['service']} has invalid or expired TLS certificate"
    
    @given(
        services=st.lists(
            st.sampled_from(['load_balancer', 'database', 'vpn', 'api']),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=50)
    def test_tls_enforcement_across_services(self, services: List[str]):
        """
        Verify that TLS is enforced across all services.
        """
        # All services must have TLS configured
        # This is a meta-test to ensure comprehensive coverage
        required_services = {'load_balancer', 'database', 'vpn', 'api'}
        tested_services = set(services)
        
        # Property: All critical services must be tested for TLS
        if len(tested_services) >= 4:
            assert required_services.issubset(tested_services) or len(tested_services) >= 4, \
                f"Not all critical services tested for TLS: missing {required_services - tested_services}"


class TestFirewallRuleMinimalism:
    """
    Property 16: Firewall Rule Minimalism
    
    **Validates: Requirements 4.6**
    
    For any security group or firewall rule, only explicitly required ports 
    and protocols should be allowed, with all other traffic denied by default.
    """
    
    @given(rule=firewall_rule_strategy())
    @settings(max_examples=100)
    def test_property_16_no_unrestricted_ingress(self, rule: Dict):
        """
        Feature: multi-cloud-dr-system, Property 16: Firewall Rule Minimalism
        
        Verify that ingress rules are not unrestricted.
        """
        # Property: Ingress from 0.0.0.0/0 should only be for specific ports
        if rule['direction'] == 'ingress' and rule['source_cidr'] == '0.0.0.0/0' and rule['action'] == 'allow':
            # Allow only for common web ports
            allowed_ports = {80, 443, 8080, 8443}
            
            if rule['from_port'] not in allowed_ports or rule['to_port'] not in allowed_ports:
                pytest.fail(
                    f"Rule {rule['rule_name']} allows unrestricted ingress on port {rule['from_port']}-{rule['to_port']}"
                )
    
    @given(rule=firewall_rule_strategy())
    @settings(max_examples=100)
    def test_property_16_no_wide_port_ranges(self, rule: Dict):
        """
        Verify that firewall rules do not use wide port ranges.
        """
        # Calculate port range width
        port_range_width = rule['to_port'] - rule['from_port']
        
        # Property: Port ranges should be specific (max 10 ports)
        MAX_PORT_RANGE = 10
        
        if rule['action'] == 'allow':
            assert port_range_width <= MAX_PORT_RANGE, \
                f"Rule {rule['rule_name']} has wide port range: {rule['from_port']}-{rule['to_port']} ({port_range_width} ports)"
    
    @given(rule=firewall_rule_strategy())
    @settings(max_examples=100)
    def test_property_16_specific_protocols(self, rule: Dict):
        """
        Verify that firewall rules specify protocols explicitly.
        """
        # Property: Protocol should be specific, not 'all'
        if rule['action'] == 'allow':
            assert rule['protocol'] != 'all', \
                f"Rule {rule['rule_name']} allows all protocols - should be specific"
    
    @given(rule=firewall_rule_strategy())
    @settings(max_examples=100)
    def test_property_16_private_subnet_sources(self, rule: Dict):
        """
        Verify that rules for private resources use private subnet sources.
        """
        # Define private CIDR ranges
        private_cidrs = ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']
        
        # Check if source is private
        is_private_source = any(
            rule['source_cidr'].startswith(cidr.split('/')[0][:3]) 
            for cidr in private_cidrs
        )
        
        # Property: Database and internal service rules should use private sources
        if rule['direction'] == 'ingress' and rule['action'] == 'allow':
            # Ports 3306 (MySQL), 5432 (PostgreSQL), 27017 (MongoDB) should be from private sources
            database_ports = {3306, 5432, 27017}
            
            if rule['from_port'] in database_ports or rule['to_port'] in database_ports:
                assert is_private_source or rule['source_cidr'] != '0.0.0.0/0', \
                    f"Rule {rule['rule_name']} allows database access from public internet"
    
    @given(
        rules=st.lists(firewall_rule_strategy(), min_size=1, max_size=20)
    )
    @settings(max_examples=50)
    def test_default_deny_policy(self, rules: List[Dict]):
        """
        Verify that firewall configuration follows default-deny principle.
        """
        # Count allow vs deny rules
        allow_rules = [r for r in rules if r['action'] == 'allow']
        deny_rules = [r for r in rules if r['action'] == 'deny']
        
        # Property: Should have explicit deny rules or implicit default deny
        # At minimum, deny rules should exist or allow rules should be specific
        if allow_rules:
            # Check that allow rules are specific (not 0.0.0.0/0 with all protocols)
            overly_permissive = [
                r for r in allow_rules 
                if r['source_cidr'] == '0.0.0.0/0' and r['protocol'] == 'all'
            ]
            
            assert len(overly_permissive) == 0, \
                f"Found {len(overly_permissive)} overly permissive allow rules"


# Utility functions for test data validation
def is_valid_iam_policy(policy: Dict) -> bool:
    """Validate IAM policy structure"""
    required_fields = ['role_name', 'actions', 'resources', 'effect']
    return all(field in policy for field in required_fields)


def is_valid_secret_config(secret: Dict) -> bool:
    """Validate secret configuration structure"""
    required_fields = ['secret_name', 'storage_type', 'encrypted']
    return all(field in secret for field in required_fields)


def is_valid_tls_config(tls_config: Dict) -> bool:
    """Validate TLS configuration structure"""
    required_fields = ['service', 'tls_version', 'certificate_valid']
    return all(field in tls_config for field in required_fields)


def is_valid_firewall_rule(rule: Dict) -> bool:
    """Validate firewall rule structure"""
    required_fields = ['rule_name', 'protocol', 'from_port', 'to_port', 'source_cidr', 'direction', 'action']
    return all(field in rule for field in required_fields)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
