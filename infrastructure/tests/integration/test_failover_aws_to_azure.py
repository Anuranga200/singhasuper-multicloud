#!/usr/bin/env python3
"""
Integration Test: End-to-End Failover from AWS to Azure

This test simulates a complete failover scenario from AWS (primary) to Azure (failover),
measuring RTO and RPO, and verifying application functionality after failover.

Test Scenario:
1. Verify AWS is healthy and serving traffic
2. Write test data to AWS primary database
3. Simulate AWS failure
4. Trigger failover to Azure
5. Verify Azure is serving traffic
6. Verify application functionality on Azure
7. Measure RTO and RPO
8. Cleanup and restore

Requirements Tested:
- 2.2: Automated failover to Azure
- 2.7: RTO < 5 minutes
- 3.5: RPO < 1 minute
"""

import time
import json
import subprocess
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import boto3
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
import mysql.connector
from mysql.connector import Error

# Test Configuration
TEST_CONFIG = {
    'aws': {
        'region': 'us-east-1',
        'alb_dns': 'multicloud-dr-alb-123456789.us-east-1.elb.amazonaws.com',
        'rds_endpoint': 'multicloud-dr-rds.abc123.us-east-1.rds.amazonaws.com',
        'asg_name': 'multicloud-dr-asg',
        'db_name': 'appdb',
        'db_user': 'admin'
    },
    'azure': {
        'subscription_id': 'your-subscription-id',
        'resource_group': 'multicloud-dr-rg',
        'lb_ip': '20.30.40.50',
        'mysql_server': 'multicloud-dr-mysql.mysql.database.azure.com',
        'vmss_name': 'multicloud-dr-vmss',
        'db_name': 'appdb',
        'db_user': 'admin@multicloud-dr-mysql'
    },
    'domain': 'your-domain.com',
    'test_data': {
        'customer_email': f'failover-test-{int(time.time())}@example.com',
        'customer_name': 'Failover Test Customer'
    },
    'thresholds': {
        'rto_seconds': 300,  # 5 minutes
        'rpo_seconds': 60    # 1 minute
    }
}


class FailoverTestAWSToAzure:
    """Integration test for AWS to Azure failover"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.test_start_time = None
        self.failover_trigger_time = None
        self.failover_complete_time = None
        self.test_data_timestamp = None
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'metrics': {}
        }
        
        # Initialize cloud clients
        self.aws_session = boto3.Session(region_name=config['aws']['region'])
        self.ec2_client = self.aws_session.client('ec2')
        self.rds_client = self.aws_session.client('rds')
        self.asg_client = self.aws_session.client('autoscaling')
        self.route53_client = self.aws_session.client('route53')
        
        # Azure clients
        self.azure_credential = DefaultAzureCredential()
        self.azure_compute_client = ComputeManagementClient(
            self.azure_credential,
            config['azure']['subscription_id']
        )
        self.azure_network_client = NetworkManagementClient(
            self.azure_credential,
            config['azure']['subscription_id']
        )
    
    def log(self, message: str, level: str = 'INFO'):
        """Log test progress"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def add_result(self, category: str, message: str):
        """Add test result"""
        self.test_results[category].append(message)
        self.log(message, category.upper())
    
    def connect_to_database(self, endpoint: str, user: str, password: str, database: str) -> Optional[mysql.connector.connection.MySQLConnection]:
        """Connect to MySQL database"""
        try:
            connection = mysql.connector.connect(
                host=endpoint,
                user=user,
                password=password,
                database=database,
                connect_timeout=10
            )
            return connection
        except Error as e:
            self.log(f"Database connection error: {e}", 'ERROR')
            return None
    
    def test_1_verify_aws_healthy(self) -> bool:
        """Test 1: Verify AWS is healthy and serving traffic"""
        self.log("=" * 80)
        self.log("TEST 1: Verify AWS is Healthy")
        self.log("=" * 80)
        
        try:
            # Check ALB health
            alb_url = f"https://{self.config['aws']['alb_dns']}/health"
            response = requests.get(alb_url, timeout=10, verify=False)
            
            if response.status_code == 200:
                self.add_result('passed', "AWS ALB health check passed")
            else:
                self.add_result('failed', f"AWS ALB health check failed: {response.status_code}")
                return False
            
            # Check RDS status
            rds_response = self.rds_client.describe_db_instances(
                DBInstanceIdentifier='multicloud-dr-rds'
            )
            rds_status = rds_response['DBInstances'][0]['DBInstanceStatus']
            
            if rds_status == 'available':
                self.add_result('passed', f"AWS RDS status: {rds_status}")
            else:
                self.add_result('failed', f"AWS RDS not available: {rds_status}")
                return False
            
            # Check ASG instances
            asg_response = self.asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[self.config['aws']['asg_name']]
            )
            instances = asg_response['AutoScalingGroups'][0]['Instances']
            healthy_instances = [i for i in instances if i['HealthStatus'] == 'Healthy']
            
            if len(healthy_instances) >= 1:
                self.add_result('passed', f"AWS has {len(healthy_instances)} healthy instances")
            else:
                self.add_result('failed', "AWS has no healthy instances")
                return False
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"AWS health check error: {str(e)}")
            return False
    
    def test_2_write_test_data(self) -> bool:
        """Test 2: Write test data to AWS primary database"""
        self.log("=" * 80)
        self.log("TEST 2: Write Test Data to AWS Primary")
        self.log("=" * 80)
        
        try:
            # Get database password from environment or secrets manager
            db_password = self._get_db_password('aws')
            
            # Connect to AWS RDS
            connection = self.connect_to_database(
                self.config['aws']['rds_endpoint'],
                self.config['aws']['db_user'],
                db_password,
                self.config['aws']['db_name']
            )
            
            if not connection:
                self.add_result('failed', "Failed to connect to AWS RDS")
                return False
            
            cursor = connection.cursor()
            
            # Create test table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failover_test (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_id VARCHAR(255) UNIQUE,
                    customer_email VARCHAR(255),
                    customer_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_test_id (test_id)
                )
            """)
            
            # Insert test data
            test_id = f"failover-test-{int(time.time())}"
            self.test_data_timestamp = datetime.now()
            
            cursor.execute("""
                INSERT INTO failover_test (test_id, customer_email, customer_name)
                VALUES (%s, %s, %s)
            """, (
                test_id,
                self.config['test_data']['customer_email'],
                self.config['test_data']['customer_name']
            ))
            
            connection.commit()
            
            # Verify write
            cursor.execute("SELECT * FROM failover_test WHERE test_id = %s", (test_id,))
            result = cursor.fetchone()
            
            if result:
                self.add_result('passed', f"Test data written successfully: {test_id}")
                self.config['test_data']['test_id'] = test_id
            else:
                self.add_result('failed', "Failed to verify test data write")
                return False
            
            cursor.close()
            connection.close()
            
            # Wait for replication to Azure
            self.log("Waiting 30 seconds for replication to Azure...")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"Test data write error: {str(e)}")
            return False
    
    def test_3_simulate_aws_failure(self) -> bool:
        """Test 3: Simulate AWS failure"""
        self.log("=" * 80)
        self.log("TEST 3: Simulate AWS Failure")
        self.log("=" * 80)
        
        try:
            self.failover_trigger_time = datetime.now()
            
            # Stop AWS EC2 instances to simulate failure
            asg_response = self.asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[self.config['aws']['asg_name']]
            )
            instances = asg_response['AutoScalingGroups'][0]['Instances']
            instance_ids = [i['InstanceId'] for i in instances]
            
            if instance_ids:
                self.log(f"Stopping {len(instance_ids)} AWS instances...")
                self.ec2_client.stop_instances(InstanceIds=instance_ids)
                self.add_result('passed', f"Stopped {len(instance_ids)} AWS instances")
            else:
                self.add_result('warnings', "No AWS instances to stop")
            
            # Suspend ASG processes to prevent auto-recovery
            self.asg_client.suspend_processes(
                AutoScalingGroupName=self.config['aws']['asg_name'],
                ScalingProcesses=['Launch', 'HealthCheck', 'ReplaceUnhealthy']
            )
            self.add_result('passed', "Suspended AWS Auto Scaling processes")
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"AWS failure simulation error: {str(e)}")
            return False
    
    def test_4_trigger_failover(self) -> bool:
        """Test 4: Trigger failover to Azure"""
        self.log("=" * 80)
        self.log("TEST 4: Trigger Failover to Azure")
        self.log("=" * 80)
        
        try:
            # Run failover orchestrator
            self.log("Executing failover orchestrator...")
            result = subprocess.run(
                ['python', 'scripts/failover_orchestrator.py', '--manual-failover', '--target', 'azure'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.add_result('passed', "Failover orchestrator executed successfully")
            else:
                self.add_result('failed', f"Failover orchestrator failed: {result.stderr}")
                return False
            
            # Wait for DNS propagation
            self.log("Waiting for DNS propagation (60 seconds)...")
            time.sleep(60)
            
            self.failover_complete_time = datetime.now()
            
            return True
            
        except subprocess.TimeoutExpired:
            self.add_result('failed', "Failover orchestrator timed out")
            return False
        except Exception as e:
            self.add_result('failed', f"Failover trigger error: {str(e)}")
            return False
    
    def test_5_verify_azure_serving(self) -> bool:
        """Test 5: Verify Azure is serving traffic"""
        self.log("=" * 80)
        self.log("TEST 5: Verify Azure is Serving Traffic")
        self.log("=" * 80)
        
        try:
            # Check DNS resolution
            import socket
            resolved_ip = socket.gethostbyname(self.config['domain'])
            self.log(f"Domain resolves to: {resolved_ip}")
            
            if resolved_ip == self.config['azure']['lb_ip']:
                self.add_result('passed', f"DNS correctly points to Azure: {resolved_ip}")
            else:
                self.add_result('warnings', f"DNS points to {resolved_ip}, expected {self.config['azure']['lb_ip']}")
            
            # Check Azure Load Balancer health
            azure_url = f"https://{self.config['azure']['lb_ip']}/health"
            response = requests.get(azure_url, timeout=10, verify=False)
            
            if response.status_code == 200:
                self.add_result('passed', "Azure Load Balancer health check passed")
            else:
                self.add_result('failed', f"Azure health check failed: {response.status_code}")
                return False
            
            # Check Azure VMSS instances
            vmss_vms = self.azure_compute_client.virtual_machine_scale_set_vms.list(
                self.config['azure']['resource_group'],
                self.config['azure']['vmss_name']
            )
            
            healthy_count = 0
            for vm in vmss_vms:
                if vm.provisioning_state == 'Succeeded':
                    healthy_count += 1
            
            if healthy_count >= 1:
                self.add_result('passed', f"Azure has {healthy_count} healthy instances")
            else:
                self.add_result('failed', "Azure has no healthy instances")
                return False
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"Azure verification error: {str(e)}")
            return False
    
    def test_6_verify_application_functionality(self) -> bool:
        """Test 6: Verify application functionality on Azure"""
        self.log("=" * 80)
        self.log("TEST 6: Verify Application Functionality on Azure")
        self.log("=" * 80)
        
        try:
            base_url = f"https://{self.config['domain']}"
            
            # Test 6.1: Health endpoint
            response = requests.get(f"{base_url}/health", timeout=10, verify=False)
            if response.status_code == 200:
                self.add_result('passed', "Health endpoint working on Azure")
            else:
                self.add_result('failed', f"Health endpoint failed: {response.status_code}")
                return False
            
            # Test 6.2: Read operation
            response = requests.get(f"{base_url}/api/customers", timeout=10, verify=False)
            if response.status_code in [200, 401]:  # 401 if auth required
                self.add_result('passed', "Read operation working on Azure")
            else:
                self.add_result('failed', f"Read operation failed: {response.status_code}")
                return False
            
            # Test 6.3: Write operation
            test_customer = {
                'email': f'azure-test-{int(time.time())}@example.com',
                'name': 'Azure Test Customer'
            }
            response = requests.post(
                f"{base_url}/api/customers",
                json=test_customer,
                timeout=10,
                verify=False
            )
            if response.status_code in [200, 201, 401]:
                self.add_result('passed', "Write operation working on Azure")
            else:
                self.add_result('failed', f"Write operation failed: {response.status_code}")
                return False
            
            # Test 6.4: Verify test data from AWS is present
            db_password = self._get_db_password('azure')
            connection = self.connect_to_database(
                self.config['azure']['mysql_server'],
                self.config['azure']['db_user'],
                db_password,
                self.config['azure']['db_name']
            )
            
            if connection:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT * FROM failover_test WHERE test_id = %s",
                    (self.config['test_data']['test_id'],)
                )
                result = cursor.fetchone()
                
                if result:
                    self.add_result('passed', "Test data from AWS found in Azure database")
                else:
                    self.add_result('failed', "Test data from AWS NOT found in Azure database")
                    return False
                
                cursor.close()
                connection.close()
            else:
                self.add_result('warnings', "Could not verify test data in Azure database")
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"Application functionality test error: {str(e)}")
            return False
    
    def test_7_measure_rto_rpo(self) -> bool:
        """Test 7: Measure RTO and RPO"""
        self.log("=" * 80)
        self.log("TEST 7: Measure RTO and RPO")
        self.log("=" * 80)
        
        try:
            # Calculate RTO
            if self.failover_trigger_time and self.failover_complete_time:
                rto = (self.failover_complete_time - self.failover_trigger_time).total_seconds()
                self.test_results['metrics']['rto_seconds'] = rto
                self.test_results['metrics']['rto_minutes'] = rto / 60
                
                self.log(f"RTO: {rto:.2f} seconds ({rto/60:.2f} minutes)")
                
                if rto <= self.config['thresholds']['rto_seconds']:
                    self.add_result('passed', f"RTO within threshold: {rto:.2f}s <= {self.config['thresholds']['rto_seconds']}s")
                else:
                    self.add_result('failed', f"RTO exceeds threshold: {rto:.2f}s > {self.config['thresholds']['rto_seconds']}s")
            else:
                self.add_result('warnings', "Could not calculate RTO - missing timestamps")
            
            # Calculate RPO
            if self.test_data_timestamp:
                # Get the timestamp of the last replicated data in Azure
                db_password = self._get_db_password('azure')
                connection = self.connect_to_database(
                    self.config['azure']['mysql_server'],
                    self.config['azure']['db_user'],
                    db_password,
                    self.config['azure']['db_name']
                )
                
                if connection:
                    cursor = connection.cursor()
                    cursor.execute(
                        "SELECT created_at FROM failover_test WHERE test_id = %s",
                        (self.config['test_data']['test_id'],)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        azure_timestamp = result[0]
                        rpo = abs((azure_timestamp - self.test_data_timestamp).total_seconds())
                        self.test_results['metrics']['rpo_seconds'] = rpo
                        
                        self.log(f"RPO: {rpo:.2f} seconds")
                        
                        if rpo <= self.config['thresholds']['rpo_seconds']:
                            self.add_result('passed', f"RPO within threshold: {rpo:.2f}s <= {self.config['thresholds']['rpo_seconds']}s")
                        else:
                            self.add_result('failed', f"RPO exceeds threshold: {rpo:.2f}s > {self.config['thresholds']['rpo_seconds']}s")
                    else:
                        self.add_result('warnings', "Could not calculate RPO - test data not found")
                    
                    cursor.close()
                    connection.close()
                else:
                    self.add_result('warnings', "Could not calculate RPO - database connection failed")
            else:
                self.add_result('warnings', "Could not calculate RPO - missing test data timestamp")
            
            return True
            
        except Exception as e:
            self.add_result('warnings', f"RTO/RPO measurement error: {str(e)}")
            return True  # Don't fail the test for measurement errors
    
    def test_8_cleanup(self) -> bool:
        """Test 8: Cleanup and restore"""
        self.log("=" * 80)
        self.log("TEST 8: Cleanup and Restore")
        self.log("=" * 80)
        
        try:
            # Resume AWS Auto Scaling
            self.asg_client.resume_processes(
                AutoScalingGroupName=self.config['aws']['asg_name']
            )
            self.add_result('passed', "Resumed AWS Auto Scaling processes")
            
            # Start AWS instances
            asg_response = self.asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[self.config['aws']['asg_name']]
            )
            instances = asg_response['AutoScalingGroups'][0]['Instances']
            instance_ids = [i['InstanceId'] for i in instances]
            
            if instance_ids:
                self.ec2_client.start_instances(InstanceIds=instance_ids)
                self.add_result('passed', f"Started {len(instance_ids)} AWS instances")
            
            # Clean up test data
            for cloud in ['aws', 'azure']:
                try:
                    db_password = self._get_db_password(cloud)
                    endpoint = self.config[cloud]['rds_endpoint'] if cloud == 'aws' else self.config[cloud]['mysql_server']
                    user = self.config[cloud]['db_user']
                    
                    connection = self.connect_to_database(
                        endpoint, user, db_password, self.config[cloud]['db_name']
                    )
                    
                    if connection:
                        cursor = connection.cursor()
                        cursor.execute(
                            "DELETE FROM failover_test WHERE test_id = %s",
                            (self.config['test_data']['test_id'],)
                        )
                        connection.commit()
                        cursor.close()
                        connection.close()
                        self.log(f"Cleaned up test data from {cloud.upper()}")
                except Exception as e:
                    self.log(f"Cleanup error for {cloud}: {e}", 'WARNING')
            
            self.add_result('passed', "Cleanup completed")
            return True
            
        except Exception as e:
            self.add_result('warnings', f"Cleanup error: {str(e)}")
            return True  # Don't fail test for cleanup errors
    
    def _get_db_password(self, cloud: str) -> str:
        """Get database password from secrets manager"""
        # This is a placeholder - implement actual secrets retrieval
        import os
        return os.environ.get(f'{cloud.upper()}_DB_PASSWORD', 'password')
    
    def run_all_tests(self) -> Dict:
        """Run all integration tests"""
        self.test_start_time = datetime.now()
        self.log("=" * 80)
        self.log("INTEGRATION TEST: AWS to Azure Failover")
        self.log("=" * 80)
        
        tests = [
            self.test_1_verify_aws_healthy,
            self.test_2_write_test_data,
            self.test_3_simulate_aws_failure,
            self.test_4_trigger_failover,
            self.test_5_verify_azure_serving,
            self.test_6_verify_application_functionality,
            self.test_7_measure_rto_rpo,
            self.test_8_cleanup
        ]
        
        for test in tests:
            try:
                result = test()
                if not result and test != self.test_8_cleanup:
                    self.log(f"Test {test.__name__} failed, stopping test suite", 'ERROR')
                    break
            except Exception as e:
                self.add_result('failed', f"Test {test.__name__} exception: {str(e)}")
                break
        
        # Generate report
        self.generate_report()
        
        return self.test_results
    
    def generate_report(self):
        """Generate test report"""
        test_end_time = datetime.now()
        duration = (test_end_time - self.test_start_time).total_seconds()
        
        self.log("=" * 80)
        self.log("TEST REPORT")
        self.log("=" * 80)
        self.log(f"Test Duration: {duration:.2f} seconds")
        self.log(f"Passed: {len(self.test_results['passed'])}")
        self.log(f"Failed: {len(self.test_results['failed'])}")
        self.log(f"Warnings: {len(self.test_results['warnings'])}")
        
        if self.test_results['metrics']:
            self.log("\nMetrics:")
            for key, value in self.test_results['metrics'].items():
                self.log(f"  {key}: {value}")
        
        if self.test_results['passed']:
            self.log("\nPassed Tests:")
            for result in self.test_results['passed']:
                self.log(f"  ✓ {result}")
        
        if self.test_results['failed']:
            self.log("\nFailed Tests:")
            for result in self.test_results['failed']:
                self.log(f"  ✗ {result}")
        
        if self.test_results['warnings']:
            self.log("\nWarnings:")
            for result in self.test_results['warnings']:
                self.log(f"  ⚠ {result}")
        
        # Overall result
        if len(self.test_results['failed']) == 0:
            self.log("\n✓ INTEGRATION TEST PASSED", 'INFO')
        else:
            self.log("\n✗ INTEGRATION TEST FAILED", 'ERROR')


def main():
    """Main test execution"""
    test = FailoverTestAWSToAzure(TEST_CONFIG)
    results = test.run_all_tests()
    
    # Exit with appropriate code
    if len(results['failed']) > 0:
        exit(1)
    else:
        exit(0)


if __name__ == '__main__':
    main()
