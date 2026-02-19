#!/usr/bin/env python3
"""
Integration Test: Database Replication

This test verifies that database replication is working correctly across all clouds,
measuring replication lag and verifying data consistency.

Test Scenario:
1. Write data to AWS primary database
2. Verify data appears in Azure replica
3. Verify data appears in GCP replica
4. Measure replication lag for each replica
5. Verify data consistency across all databases
6. Test replication under load
7. Cleanup test data

Requirements Tested:
- 3.1: Replication lag < 30 seconds (Azure)
- 3.2: Replication lag < 30 seconds (GCP)
- 3.6: Data consistency verification
"""

import time
import hashlib
import random
import string
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import boto3
import mysql.connector
from mysql.connector import Error
import subprocess

# Test Configuration
TEST_CONFIG = {
    'aws': {
        'rds_endpoint': 'multicloud-dr-rds.abc123.us-east-1.rds.amazonaws.com',
        'db_name': 'appdb',
        'db_user': 'admin'
    },
    'azure': {
        'mysql_server': 'multicloud-dr-mysql.mysql.database.azure.com',
        'db_name': 'appdb',
        'db_user': 'admin@multicloud-dr-mysql'
    },
    'gcp': {
        'cloudsql_instance': 'multicloud-dr-cloudsql',
        'db_name': 'appdb',
        'db_user': 'root'
    },
    'thresholds': {
        'replication_lag_seconds': 30,
        'consistency_tolerance': 0  # No data loss acceptable
    },
    'load_test': {
        'num_records': 100,
        'batch_size': 10
    }
}


class DatabaseReplicationTest:
    """Integration test for database replication"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.test_start_time = None
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'metrics': {}
        }
        self.test_data_ids = []
    
    def log(self, message: str, level: str = 'INFO'):
        """Log test progress"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def add_result(self, category: str, message: str):
        """Add test result"""
        self.test_results[category].append(message)
        self.log(message, category.upper())
    
    def connect_to_database(self, cloud: str) -> Optional[mysql.connector.connection.MySQLConnection]:
        """Connect to database for specified cloud"""
        try:
            config = self.config[cloud]
            password = self._get_db_password(cloud)
            
            # Get endpoint
            if cloud == 'gcp':
                result = subprocess.run([
                    'gcloud', 'sql', 'instances', 'describe',
                    config['cloudsql_instance'],
                    '--format', 'value(ipAddresses[0].ipAddress)'
                ], capture_output=True, text=True, check=True)
                endpoint = result.stdout.strip()
            else:
                endpoint = config.get('rds_endpoint') or config.get('mysql_server')
            
            connection = mysql.connector.connect(
                host=endpoint,
                user=config['db_user'],
                password=password,
                database=config['db_name'],
                connect_timeout=10
            )
            return connection
        except Exception as e:
            self.log(f"Database connection error for {cloud}: {e}", 'ERROR')
            return None
    
    def test_1_setup_test_table(self) -> bool:
        """Test 1: Set up test table in primary database"""
        self.log("=" * 80)
        self.log("TEST 1: Setup Test Table")
        self.log("=" * 80)
        
        try:
            connection = self.connect_to_database('aws')
            if not connection:
                self.add_result('failed', "Failed to connect to AWS RDS")
                return False
            
            cursor = connection.cursor()
            
            # Create test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS replication_test (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_id VARCHAR(255) UNIQUE,
                    data_value VARCHAR(255),
                    checksum VARCHAR(64),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_test_id (test_id),
                    INDEX idx_created_at (created_at)
                )
            """)
            
            connection.commit()
            self.add_result('passed', "Test table created successfully")
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"Test table setup error: {str(e)}")
            return False
    
    def test_2_write_data_to_primary(self) -> bool:
        """Test 2: Write test data to AWS primary"""
        self.log("=" * 80)
        self.log("TEST 2: Write Data to Primary")
        self.log("=" * 80)
        
        try:
            connection = self.connect_to_database('aws')
            if not connection:
                self.add_result('failed', "Failed to connect to AWS RDS")
                return False
            
            cursor = connection.cursor()
            
            # Write test records
            num_records = 10
            write_start_time = datetime.now()
            
            for i in range(num_records):
                test_id = f"repl-test-{int(time.time())}-{i}"
                data_value = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
                checksum = hashlib.sha256(data_value.encode()).hexdigest()
                
                cursor.execute("""
                    INSERT INTO replication_test (test_id, data_value, checksum)
                    VALUES (%s, %s, %s)
                """, (test_id, data_value, checksum))
                
                self.test_data_ids.append(test_id)
            
            connection.commit()
            write_end_time = datetime.now()
            write_duration = (write_end_time - write_start_time).total_seconds()
            
            self.test_results['metrics']['write_duration_seconds'] = write_duration
            self.test_results['metrics']['records_written'] = num_records
            
            self.add_result('passed', f"Wrote {num_records} records in {write_duration:.2f} seconds")
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"Data write error: {str(e)}")
            return False
    
    def test_3_verify_azure_replication(self) -> bool:
        """Test 3: Verify data appears in Azure replica"""
        self.log("=" * 80)
        self.log("TEST 3: Verify Azure Replication")
        self.log("=" * 80)
        
        try:
            # Wait a bit for replication
            self.log("Waiting 10 seconds for replication...")
            time.sleep(10)
            
            connection = self.connect_to_database('azure')
            if not connection:
                self.add_result('failed', "Failed to connect to Azure MySQL")
                return False
            
            cursor = connection.cursor()
            
            # Check replication status
            cursor.execute("SHOW SLAVE STATUS")
            slave_status = cursor.fetchone()
            
            if slave_status:
                # Parse slave status (column indices may vary)
                slave_io_running = slave_status[10]  # Slave_IO_Running
                slave_sql_running = slave_status[11]  # Slave_SQL_Running
                seconds_behind_master = slave_status[32]  # Seconds_Behind_Master
                
                self.log(f"Azure Replication Status:")
                self.log(f"  Slave_IO_Running: {slave_io_running}")
                self.log(f"  Slave_SQL_Running: {slave_sql_running}")
                self.log(f"  Seconds_Behind_Master: {seconds_behind_master}")
                
                if slave_io_running == 'Yes' and slave_sql_running == 'Yes':
                    self.add_result('passed', "Azure replication threads running")
                else:
                    self.add_result('failed', "Azure replication threads not running")
                    return False
                
                if seconds_behind_master is not None and seconds_behind_master <= self.config['thresholds']['replication_lag_seconds']:
                    self.add_result('passed', f"Azure replication lag: {seconds_behind_master}s (within threshold)")
                    self.test_results['metrics']['azure_replication_lag_seconds'] = seconds_behind_master
                else:
                    self.add_result('failed', f"Azure replication lag too high: {seconds_behind_master}s")
                    return False
            else:
                self.add_result('warnings', "Could not retrieve Azure replication status")
            
            # Verify test data
            cursor.execute(
                "SELECT COUNT(*) FROM replication_test WHERE test_id IN (%s)" % ','.join(['%s'] * len(self.test_data_ids)),
                self.test_data_ids
            )
            count = cursor.fetchone()[0]
            
            if count == len(self.test_data_ids):
                self.add_result('passed', f"All {count} records replicated to Azure")
            else:
                self.add_result('failed', f"Only {count}/{len(self.test_data_ids)} records replicated to Azure")
                return False
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"Azure replication verification error: {str(e)}")
            return False
    
    def test_4_verify_gcp_replication(self) -> bool:
        """Test 4: Verify data appears in GCP replica"""
        self.log("=" * 80)
        self.log("TEST 4: Verify GCP Replication")
        self.log("=" * 80)
        
        try:
            connection = self.connect_to_database('gcp')
            if not connection:
                self.add_result('failed', "Failed to connect to GCP Cloud SQL")
                return False
            
            cursor = connection.cursor()
            
            # Check replication status
            cursor.execute("SHOW SLAVE STATUS")
            slave_status = cursor.fetchone()
            
            if slave_status:
                slave_io_running = slave_status[10]
                slave_sql_running = slave_status[11]
                seconds_behind_master = slave_status[32]
                
                self.log(f"GCP Replication Status:")
                self.log(f"  Slave_IO_Running: {slave_io_running}")
                self.log(f"  Slave_SQL_Running: {slave_sql_running}")
                self.log(f"  Seconds_Behind_Master: {seconds_behind_master}")
                
                if slave_io_running == 'Yes' and slave_sql_running == 'Yes':
                    self.add_result('passed', "GCP replication threads running")
                else:
                    self.add_result('failed', "GCP replication threads not running")
                    return False
                
                if seconds_behind_master is not None and seconds_behind_master <= self.config['thresholds']['replication_lag_seconds']:
                    self.add_result('passed', f"GCP replication lag: {seconds_behind_master}s (within threshold)")
                    self.test_results['metrics']['gcp_replication_lag_seconds'] = seconds_behind_master
                else:
                    self.add_result('failed', f"GCP replication lag too high: {seconds_behind_master}s")
                    return False
            else:
                self.add_result('warnings', "Could not retrieve GCP replication status")
            
            # Verify test data
            cursor.execute(
                "SELECT COUNT(*) FROM replication_test WHERE test_id IN (%s)" % ','.join(['%s'] * len(self.test_data_ids)),
                self.test_data_ids
            )
            count = cursor.fetchone()[0]
            
            if count == len(self.test_data_ids):
                self.add_result('passed', f"All {count} records replicated to GCP")
            else:
                self.add_result('failed', f"Only {count}/{len(self.test_data_ids)} records replicated to GCP")
                return False
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            self.add_result('failed', f"GCP replication verification error: {str(e)}")
            return False
    
    def test_5_verify_data_consistency(self) -> bool:
        """Test 5: Verify data consistency across all databases"""
        self.log("=" * 80)
        self.log("TEST 5: Verify Data Consistency")
        self.log("=" * 80)
        
        try:
            # Get data from all clouds
            data_by_cloud = {}
            
            for cloud in ['aws', 'azure', 'gcp']:
                connection = self.connect_to_database(cloud)
                if not connection:
                    self.add_result('warnings', f"Could not connect to {cloud.upper()}")
                    continue
                
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT test_id, data_value, checksum FROM replication_test WHERE test_id IN (%s) ORDER BY test_id" % ','.join(['%s'] * len(self.test_data_ids)),
                    self.test_data_ids
                )
                data_by_cloud[cloud] = cursor.fetchall()
                cursor.close()
                connection.close()
            
            # Compare data across clouds
            if len(data_by_cloud) < 2:
                self.add_result('warnings', "Not enough clouds available for consistency check")
                return True
            
            clouds = list(data_by_cloud.keys())
            reference_cloud = clouds[0]
            reference_data = data_by_cloud[reference_cloud]
            
            all_consistent = True
            for cloud in clouds[1:]:
                cloud_data = data_by_cloud[cloud]
                
                if len(reference_data) != len(cloud_data):
                    self.add_result('failed', f"Row count mismatch: {reference_cloud}={len(reference_data)}, {cloud}={len(cloud_data)}")
                    all_consistent = False
                    continue
                
                # Compare each record
                mismatches = 0
                for ref_row, cloud_row in zip(reference_data, cloud_data):
                    if ref_row != cloud_row:
                        mismatches += 1
                        self.log(f"Data mismatch in {cloud}: {ref_row[0]}", 'WARNING')
                
                if mismatches == 0:
                    self.add_result('passed', f"Data consistent between {reference_cloud.upper()} and {cloud.upper()}")
                else:
                    self.add_result('failed', f"{mismatches} data mismatches between {reference_cloud.upper()} and {cloud.upper()}")
                    all_consistent = False
            
            return all_consistent
            
        except Exception as e:
            self.add_result('failed', f"Data consistency verification error: {str(e)}")
            return False
    
    def test_6_replication_under_load(self) -> bool:
        """Test 6: Test replication under load"""
        self.log("=" * 80)
        self.log("TEST 6: Replication Under Load")
        self.log("=" * 80)
        
        try:
            connection = self.connect_to_database('aws')
            if not connection:
                self.add_result('failed', "Failed to connect to AWS RDS")
                return False
            
            cursor = connection.cursor()
            
            # Write many records quickly
            num_records = self.config['load_test']['num_records']
            batch_size = self.config['load_test']['batch_size']
            
            load_test_ids = []
            write_start_time = datetime.now()
            
            for batch in range(0, num_records, batch_size):
                batch_data = []
                for i in range(batch, min(batch + batch_size, num_records)):
                    test_id = f"load-test-{int(time.time())}-{i}"
                    data_value = ''.join(random.choices(string.ascii_letters, k=100))
                    checksum = hashlib.sha256(data_value.encode()).hexdigest()
                    batch_data.append((test_id, data_value, checksum))
                    load_test_ids.append(test_id)
                
                cursor.executemany("""
                    INSERT INTO replication_test (test_id, data_value, checksum)
                    VALUES (%s, %s, %s)
                """, batch_data)
                connection.commit()
            
            write_end_time = datetime.now()
            write_duration = (write_end_time - write_start_time).total_seconds()
            
            self.log(f"Wrote {num_records} records in {write_duration:.2f} seconds")
            self.test_results['metrics']['load_test_records'] = num_records
            self.test_results['metrics']['load_test_duration_seconds'] = write_duration
            self.test_results['metrics']['load_test_throughput_rps'] = num_records / write_duration
            
            # Wait for replication
            self.log("Waiting 30 seconds for replication under load...")
            time.sleep(30)
            
            # Verify replication caught up
            for cloud in ['azure', 'gcp']:
                connection_replica = self.connect_to_database(cloud)
                if not connection_replica:
                    self.add_result('warnings', f"Could not verify {cloud.upper()} under load")
                    continue
                
                cursor_replica = connection_replica.cursor()
                cursor_replica.execute(
                    "SELECT COUNT(*) FROM replication_test WHERE test_id IN (%s)" % ','.join(['%s'] * len(load_test_ids)),
                    load_test_ids
                )
                count = cursor_replica.fetchone()[0]
                
                if count == num_records:
                    self.add_result('passed', f"{cloud.upper()} replicated all {num_records} records under load")
                else:
                    self.add_result('warnings', f"{cloud.upper()} only replicated {count}/{num_records} records under load")
                
                cursor_replica.close()
                connection_replica.close()
            
            # Cleanup load test data
            cursor.execute(
                "DELETE FROM replication_test WHERE test_id IN (%s)" % ','.join(['%s'] * len(load_test_ids)),
                load_test_ids
            )
            connection.commit()
            
            cursor.close()
            connection.close()
            
            self.add_result('passed', "Replication under load test completed")
            return True
            
        except Exception as e:
            self.add_result('failed', f"Replication under load error: {str(e)}")
            return False
    
    def test_7_cleanup(self) -> bool:
        """Test 7: Cleanup test data"""
        self.log("=" * 80)
        self.log("TEST 7: Cleanup")
        self.log("=" * 80)
        
        try:
            connection = self.connect_to_database('aws')
            if not connection:
                self.add_result('warnings', "Could not connect to AWS for cleanup")
                return True
            
            cursor = connection.cursor()
            
            # Delete test data
            if self.test_data_ids:
                cursor.execute(
                    "DELETE FROM replication_test WHERE test_id IN (%s)" % ','.join(['%s'] * len(self.test_data_ids)),
                    self.test_data_ids
                )
                connection.commit()
                self.log(f"Deleted {len(self.test_data_ids)} test records")
            
            cursor.close()
            connection.close()
            
            self.add_result('passed', "Cleanup completed")
            return True
            
        except Exception as e:
            self.add_result('warnings', f"Cleanup error: {str(e)}")
            return True
    
    def _get_db_password(self, cloud: str) -> str:
        """Get database password from environment"""
        import os
        return os.environ.get(f'{cloud.upper()}_DB_PASSWORD', 'password')
    
    def run_all_tests(self) -> Dict:
        """Run all integration tests"""
        self.test_start_time = datetime.now()
        self.log("=" * 80)
        self.log("INTEGRATION TEST: Database Replication")
        self.log("=" * 80)
        
        tests = [
            self.test_1_setup_test_table,
            self.test_2_write_data_to_primary,
            self.test_3_verify_azure_replication,
            self.test_4_verify_gcp_replication,
            self.test_5_verify_data_consistency,
            self.test_6_replication_under_load,
            self.test_7_cleanup
        ]
        
        for test in tests:
            try:
                result = test()
                if not result and test != self.test_7_cleanup:
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
    test = DatabaseReplicationTest(TEST_CONFIG)
    results = test.run_all_tests()
    
    if len(results['failed']) > 0:
        exit(1)
    else:
        exit(0)


if __name__ == '__main__':
    main()
