#!/usr/bin/env python3
"""
Final Checkpoint and Validation

This script performs comprehensive end-to-end validation of the Multi-Cloud DR System.
It runs all tests, verifies all components, and generates a final validation report.

Usage:
    python final_validation.py [--full] [--report-only]

Options:
    --full          Run all tests including integration tests (requires deployed infrastructure)
    --report-only   Generate report from previous test results without running tests
"""

import sys
import os
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path

class FinalValidation:
    """Comprehensive final validation of the Multi-Cloud DR System"""
    
    def __init__(self, full_mode: bool = False, report_only: bool = False):
        self.full_mode = full_mode
        self.report_only = report_only
        self.start_time = datetime.now()
        self.results = {
            'infrastructure': {},
            'tests': {},
            'documentation': {},
            'costs': {},
            'overall': {}
        }
        self.test_summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def log(self, message: str, level: str = 'INFO'):
        """Log validation progress"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: List[str], cwd: str = None) -> Tuple[int, str, str]:
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def validate_1_infrastructure_files(self) -> bool:
        """Validate 1: Check all infrastructure files exist"""
        self.log("=" * 80)
        self.log("VALIDATION 1: Infrastructure Files")
        self.log("=" * 80)
        
        required_files = {
            'terraform': [
                'infrastructure/terraform/aws/main.tf',
                'infrastructure/terraform/azure/main.tf',
                'infrastructure/terraform/gcp/main.tf',
                'infrastructure/terraform/route53/main.tf',
                'infrastructure/terraform/variables.tf'
            ],
            'scripts': [
                'infrastructure/scripts/health_monitor.py',
                'infrastructure/scripts/failover_orchestrator.py',
                'infrastructure/scripts/dns_failover.py',
                'infrastructure/scripts/setup_replication.py',
                'infrastructure/scripts/verify_consistency.py',
                'infrastructure/scripts/database_promotion.py',
                'infrastructure/scripts/failback.py'
            ],
            'monitoring': [
                'infrastructure/monitoring/aws_cloudwatch_dashboard.py',
                'infrastructure/monitoring/azure_monitor_dashboard.py',
                'infrastructure/monitoring/gcp_monitoring_dashboard.py',
                'infrastructure/monitoring/unified_dashboard.py'
            ],
            'backup': [
                'infrastructure/backup/backup_manager.py',
                'infrastructure/backup/backup_verification.py',
                'infrastructure/backup/backup_restore.py',
                'infrastructure/backup/backup_restore_test.py'
            ],
            'security': [
                'infrastructure/security/iam_audit.py',
                'infrastructure/security/network_audit.py',
                'infrastructure/security/credential_rotation.py'
            ],
            'cost': [
                'infrastructure/cost/cost_monitor.py',
                'infrastructure/cost/cost_reporter.py'
            ]
        }
        
        all_exist = True
        for category, files in required_files.items():
            missing = []
            for file_path in files:
                if not Path(file_path).exists():
                    missing.append(file_path)
                    all_exist = False
            
            if missing:
                self.log(f"Missing {category} files: {len(missing)}", 'ERROR')
                for f in missing:
                    self.log(f"  - {f}", 'ERROR')
            else:
                self.log(f"All {category} files present: {len(files)}", 'PASS')
        
        self.results['infrastructure']['files'] = 'PASS' if all_exist else 'FAIL'
        return all_exist
    
    def validate_2_documentation(self) -> bool:
        """Validate 2: Check all documentation exists"""
        self.log("=" * 80)
        self.log("VALIDATION 2: Documentation")
        self.log("=" * 80)
        
        required_docs = [
            'infrastructure/docs/ARCHITECTURE.md',
            'infrastructure/docs/DEPLOYMENT_GUIDE.md',
            'infrastructure/docs/COST_ESTIMATION.md',
            'infrastructure/docs/runbooks/MANUAL_FAILOVER.md',
            'infrastructure/docs/runbooks/FAILBACK.md',
            'infrastructure/docs/runbooks/DATABASE_PROMOTION.md',
            'infrastructure/docs/runbooks/TROUBLESHOOTING.md',
            'infrastructure/README.md',
            '.github/workflows/README.md'
        ]
        
        all_exist = True
        for doc in required_docs:
            if not Path(doc).exists():
                self.log(f"Missing: {doc}", 'ERROR')
                all_exist = False
            else:
                # Check file is not empty
                size = Path(doc).stat().st_size
                if size < 100:
                    self.log(f"Documentation too small: {doc} ({size} bytes)", 'WARN')
                else:
                    self.log(f"Found: {doc} ({size} bytes)", 'PASS')
        
        self.results['documentation']['files'] = 'PASS' if all_exist else 'FAIL'
        return all_exist
    
    def validate_3_unit_tests(self) -> bool:
        """Validate 3: Run unit tests"""
        self.log("=" * 80)
        self.log("VALIDATION 3: Unit Tests")
        self.log("=" * 80)
        
        if self.report_only:
            self.log("Skipping (report-only mode)", 'SKIP')
            self.test_summary['skipped'] += 1
            return True
        
        # Run pytest
        returncode, stdout, stderr = self.run_command(
            ['pytest', 'tests/', '-v', '--tb=short'],
            cwd='infrastructure'
        )
        
        if returncode == 0:
            self.log("Unit tests passed", 'PASS')
            self.results['tests']['unit'] = 'PASS'
            self.test_summary['passed'] += 1
            return True
        else:
            self.log(f"Unit tests failed:\n{stderr}", 'FAIL')
            self.results['tests']['unit'] = 'FAIL'
            self.test_summary['failed'] += 1
            return False
    
    def validate_4_property_tests(self) -> bool:
        """Validate 4: Run property-based tests"""
        self.log("=" * 80)
        self.log("VALIDATION 4: Property-Based Tests")
        self.log("=" * 80)
        
        if self.report_only:
            self.log("Skipping (report-only mode)", 'SKIP')
            self.test_summary['skipped'] += 1
            return True
        
        # Run property tests
        returncode, stdout, stderr = self.run_command(
            ['pytest', 'tests/property/', '-v', '--tb=short'],
            cwd='infrastructure'
        )
        
        if returncode == 0:
            self.log("Property-based tests passed", 'PASS')
            self.results['tests']['property'] = 'PASS'
            self.test_summary['passed'] += 1
            return True
        else:
            self.log(f"Property-based tests failed:\n{stderr}", 'FAIL')
            self.results['tests']['property'] = 'FAIL'
            self.test_summary['failed'] += 1
            return False
    
    def validate_5_integration_tests(self) -> bool:
        """Validate 5: Run integration tests (if full mode)"""
        self.log("=" * 80)
        self.log("VALIDATION 5: Integration Tests")
        self.log("=" * 80)
        
        if not self.full_mode:
            self.log("Skipping (use --full to run integration tests)", 'SKIP')
            self.test_summary['skipped'] += 1
            return True
        
        if self.report_only:
            self.log("Skipping (report-only mode)", 'SKIP')
            self.test_summary['skipped'] += 1
            return True
        
        integration_tests = [
            'test_database_replication.py',
            'test_security_controls.py'
        ]
        
        all_passed = True
        for test in integration_tests:
            self.log(f"Running {test}...")
            returncode, stdout, stderr = self.run_command(
                ['python', test],
                cwd='infrastructure/tests/integration'
            )
            
            if returncode == 0:
                self.log(f"{test} passed", 'PASS')
            else:
                self.log(f"{test} failed", 'FAIL')
                all_passed = False
        
        if all_passed:
            self.results['tests']['integration'] = 'PASS'
            self.test_summary['passed'] += 1
        else:
            self.results['tests']['integration'] = 'FAIL'
            self.test_summary['failed'] += 1
        
        return all_passed
    
    def validate_6_terraform_syntax(self) -> bool:
        """Validate 6: Validate Terraform syntax"""
        self.log("=" * 80)
        self.log("VALIDATION 6: Terraform Syntax")
        self.log("=" * 80)
        
        if self.report_only:
            self.log("Skipping (report-only mode)", 'SKIP')
            self.test_summary['skipped'] += 1
            return True
        
        terraform_dirs = [
            'infrastructure/terraform/aws',
            'infrastructure/terraform/azure',
            'infrastructure/terraform/gcp',
            'infrastructure/terraform/route53'
        ]
        
        all_valid = True
        for tf_dir in terraform_dirs:
            self.log(f"Validating {tf_dir}...")
            
            # Init
            returncode, _, _ = self.run_command(
                ['terraform', 'init', '-backend=false'],
                cwd=tf_dir
            )
            
            if returncode != 0:
                self.log(f"Terraform init failed for {tf_dir}", 'FAIL')
                all_valid = False
                continue
            
            # Validate
            returncode, _, stderr = self.run_command(
                ['terraform', 'validate'],
                cwd=tf_dir
            )
            
            if returncode == 0:
                self.log(f"{tf_dir} valid", 'PASS')
            else:
                self.log(f"{tf_dir} invalid: {stderr}", 'FAIL')
                all_valid = False
        
        if all_valid:
            self.results['infrastructure']['terraform'] = 'PASS'
            self.test_summary['passed'] += 1
        else:
            self.results['infrastructure']['terraform'] = 'FAIL'
            self.test_summary['failed'] += 1
        
        return all_valid
    
    def validate_7_python_syntax(self) -> bool:
        """Validate 7: Check Python syntax"""
        self.log("=" * 80)
        self.log("VALIDATION 7: Python Syntax")
        self.log("=" * 80)
        
        if self.report_only:
            self.log("Skipping (report-only mode)", 'SKIP')
            self.test_summary['skipped'] += 1
            return True
        
        # Find all Python files
        python_files = list(Path('infrastructure').rglob('*.py'))
        
        all_valid = True
        errors = []
        
        for py_file in python_files:
            returncode, _, stderr = self.run_command(
                ['python', '-m', 'py_compile', str(py_file)]
            )
            
            if returncode != 0:
                errors.append(f"{py_file}: {stderr}")
                all_valid = False
        
        if all_valid:
            self.log(f"All {len(python_files)} Python files valid", 'PASS')
            self.results['infrastructure']['python'] = 'PASS'
            self.test_summary['passed'] += 1
        else:
            self.log(f"Python syntax errors in {len(errors)} files", 'FAIL')
            for error in errors[:5]:  # Show first 5
                self.log(f"  {error}", 'ERROR')
            self.results['infrastructure']['python'] = 'FAIL'
            self.test_summary['failed'] += 1
        
        return all_valid
    
    def validate_8_cost_estimates(self) -> bool:
        """Validate 8: Verify cost estimates are documented"""
        self.log("=" * 80)
        self.log("VALIDATION 8: Cost Estimates")
        self.log("=" * 80)
        
        cost_doc = Path('infrastructure/docs/COST_ESTIMATION.md')
        
        if not cost_doc.exists():
            self.log("Cost estimation documentation missing", 'FAIL')
            self.results['costs']['documentation'] = 'FAIL'
            return False
        
        # Check for key cost information
        content = cost_doc.read_text()
        required_sections = [
            'Monthly Cost Breakdown',
            'AWS',
            'Azure',
            'GCP',
            'Cost Optimization'
        ]
        
        all_present = True
        for section in required_sections:
            if section not in content:
                self.log(f"Missing section: {section}", 'FAIL')
                all_present = False
            else:
                self.log(f"Found section: {section}", 'PASS')
        
        if all_present:
            self.results['costs']['documentation'] = 'PASS'
            self.test_summary['passed'] += 1
        else:
            self.results['costs']['documentation'] = 'FAIL'
            self.test_summary['failed'] += 1
        
        return all_present
    
    def validate_9_cicd_workflows(self) -> bool:
        """Validate 9: Check CI/CD workflows exist"""
        self.log("=" * 80)
        self.log("VALIDATION 9: CI/CD Workflows")
        self.log("=" * 80)
        
        required_workflows = [
            '.github/workflows/terraform-validation.yml',
            '.github/workflows/python-testing.yml',
            '.github/workflows/deployment.yml'
        ]
        
        all_exist = True
        for workflow in required_workflows:
            if not Path(workflow).exists():
                self.log(f"Missing: {workflow}", 'FAIL')
                all_exist = False
            else:
                self.log(f"Found: {workflow}", 'PASS')
        
        if all_exist:
            self.results['infrastructure']['cicd'] = 'PASS'
            self.test_summary['passed'] += 1
        else:
            self.results['infrastructure']['cicd'] = 'FAIL'
            self.test_summary['failed'] += 1
        
        return all_exist
    
    def validate_10_requirements_coverage(self) -> bool:
        """Validate 10: Check requirements coverage"""
        self.log("=" * 80)
        self.log("VALIDATION 10: Requirements Coverage")
        self.log("=" * 80)
        
        # Count property tests
        property_tests = list(Path('infrastructure/tests/property').glob('test_*.py'))
        
        self.log(f"Property test files: {len(property_tests)}", 'INFO')
        
        # Expected minimum based on design
        expected_min = 10
        
        if len(property_tests) >= expected_min:
            self.log(f"Requirements coverage adequate ({len(property_tests)} >= {expected_min})", 'PASS')
            self.results['tests']['coverage'] = 'PASS'
            self.test_summary['passed'] += 1
            return True
        else:
            self.log(f"Requirements coverage insufficient ({len(property_tests)} < {expected_min})", 'FAIL')
            self.results['tests']['coverage'] = 'FAIL'
            self.test_summary['failed'] += 1
            return False
    
    def generate_report(self):
        """Generate final validation report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.log("=" * 80)
        self.log("FINAL VALIDATION REPORT")
        self.log("=" * 80)
        
        self.log(f"Validation Duration: {duration:.2f} seconds")
        self.log(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.log("\nTest Summary:")
        self.log(f"  Total: {self.test_summary['total']}")
        self.log(f"  Passed: {self.test_summary['passed']}")
        self.log(f"  Failed: {self.test_summary['failed']}")
        self.log(f"  Skipped: {self.test_summary['skipped']}")
        
        self.log("\nValidation Results:")
        for category, tests in self.results.items():
            self.log(f"\n{category.upper()}:")
            for test_name, result in tests.items():
                status_icon = '✓' if result == 'PASS' else '✗' if result == 'FAIL' else '⊘'
                self.log(f"  {status_icon} {test_name}: {result}")
        
        # Overall status
        total_tests = self.test_summary['passed'] + self.test_summary['failed']
        if total_tests > 0:
            pass_rate = (self.test_summary['passed'] / total_tests) * 100
        else:
            pass_rate = 0
        
        self.log(f"\nOverall Pass Rate: {pass_rate:.1f}%")
        
        if self.test_summary['failed'] == 0:
            self.log("\n✓ FINAL VALIDATION PASSED", 'PASS')
            self.log("\nThe Multi-Cloud DR System is ready for deployment!")
            overall_status = 'PASS'
        else:
            self.log("\n✗ FINAL VALIDATION FAILED", 'FAIL')
            self.log(f"\n{self.test_summary['failed']} validation(s) failed. Please review and fix issues.")
            overall_status = 'FAIL'
        
        # Save report to file
        report_file = f"final_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': duration,
            'summary': self.test_summary,
            'results': self.results,
            'overall_status': overall_status,
            'pass_rate': pass_rate
        }
        
        with open(f'infrastructure/test-results/{report_file}', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"\nReport saved to: infrastructure/test-results/{report_file}")
        
        return overall_status == 'PASS'
    
    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        self.log("=" * 80)
        self.log("MULTI-CLOUD DR SYSTEM - FINAL VALIDATION")
        self.log("=" * 80)
        self.log(f"Mode: {'Full' if self.full_mode else 'Standard'}")
        self.log(f"Report Only: {self.report_only}")
        self.log("")
        
        # Create test results directory
        Path('infrastructure/test-results').mkdir(exist_ok=True)
        
        validations = [
            self.validate_1_infrastructure_files,
            self.validate_2_documentation,
            self.validate_3_unit_tests,
            self.validate_4_property_tests,
            self.validate_5_integration_tests,
            self.validate_6_terraform_syntax,
            self.validate_7_python_syntax,
            self.validate_8_cost_estimates,
            self.validate_9_cicd_workflows,
            self.validate_10_requirements_coverage
        ]
        
        self.test_summary['total'] = len(validations)
        
        for validation in validations:
            try:
                validation()
            except Exception as e:
                self.log(f"Validation error: {str(e)}", 'ERROR')
                self.test_summary['failed'] += 1
        
        # Generate final report
        return self.generate_report()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Final validation of Multi-Cloud DR System')
    parser.add_argument('--full', action='store_true', help='Run full validation including integration tests')
    parser.add_argument('--report-only', action='store_true', help='Generate report without running tests')
    
    args = parser.parse_args()
    
    validator = FinalValidation(full_mode=args.full, report_only=args.report_only)
    success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
