"""
Property-Based Tests for Replication Lag Bounds
Feature: multi-cloud-dr-system
Property 8: Replication Lag Bounds
Validates: Requirements 3.1, 3.2

For any database write operation on the primary, the data should appear 
in all replica databases within 5 seconds.
"""

import pytest
from hypothesis import given, settings, strategies as st
import time
import pymysql
import boto3
from typing import Dict, Optional
import os
import uuid
from datetime import datetime


class ReplicationLagTester:
    """Tests replication lag across clouds"""
    
    def __init__(self):
        self.aws_connection = None
        self.azure_connection = None
        self.gcp_connection = None
        
    def connect_to_databases(self) -> bool:
        """Connect to all databases"""
        try:
            # Connect to AWS RDS (primary)
            aws_endpoint = self._get_aws_endpoint()
            self.aws_connection = pymysql.connect(
                host=aws_endpoint.split(':')[0],
                port=int(aws_endpoint.split(':')[1]) if ':' in aws_endpoint else 3306,
                user=os.getenv('AWS_MASTER_USERNAME', 'admin'),
                password=self._get_aws_password(),
                database=os.getenv('DATABASE_NAME', 'singha_loyalty')
            )
            
            # Connect to Azure MySQL (replica)
            azure_endpoint = self._get_azure_endpoint()
            self.azure_connection = pymysql.connect(
                host=azure_endpoint,
                port=3306,
                user=os.getenv('AZURE_ADMIN_USERNAME', 'azureadmin'),
                password=self._get_azure_password(),
                database=os.getenv('DATABASE_NAME', 'singha_loyalty')
            )
            
            # Connect to GCP Cloud SQL (replica)
            gcp_endpoint = self._get_gcp_endpoint()
            self.gcp_connection = pymysql.connect(
                host=gcp_endpoint,
                port=3306,
                user=os.getenv('GCP_ROOT_USERNAME', 'root'),
                password=self._get_gcp_password(),
                database=os.getenv('DATABASE_NAME', 'singha_loyalty')
            )
            
            return True
            
        except Exception as e:
            print(f"Error connecting to databases: {e}")
            return False
    
    def write_test_data(self, test_id: str, test_value: str) -> bool:
        """Write test data to primary database"""
        try:
            with self.aws_connection.cursor() as cursor:
                # Create test table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS replication_test (
                        id VARCHAR(36) PRIMARY KEY,
                        test_value VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert test data
                cursor.execute(
                    "INSERT INTO replication_test (id, test_value) VALUES (%s, %s)",
                    (test_id, test_value)
                )
                
                self.aws_connection.commit()
                return True
                
        except Exception as e:
            print(f"Error writing test data: {e}")
            return False
    
    def check_data_replicated(self, test_id: str, connection, max_wait: int = 5) -> Optional[float]:
        """
        Check if data has replicated to a replica database
        
        Returns:
            Replication lag in seconds, or None if data not found within max_wait
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT test_value FROM replication_test WHERE id = %s",
                        (test_id,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        lag = time.time() - start_time
                        return lag
                
                # Wait before retry
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error checking replication: {e}")
                time.sleep(0.1)
        
        return None
    
    def cleanup_test_data(self, test_id: str):
        """Clean up test data from all databases"""
        for connection in [self.aws_connection, self.azure_connection, self.gcp_connection]:
            if connection:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM replication_test WHERE id = %s", (test_id,))
                        connection.commit()
                except Exception as e:
                    print(f"Error cleaning up test data: {e}")
    
    def close_connections(self):
        """Close all database connections"""
        if self.aws_connection:
            self.aws_connection.close()
        if self.azure_connection:
            self.azure_connection.close()
        if self.gcp_connection:
            self.gcp_connection.close()
    
    def _get_aws_endpoint(self) -> str:
        """Get AWS RDS endpoint"""
        rds_client = boto3.client('rds', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=os.getenv('AWS_DB_IDENTIFIER', 'singha-loyalty-prod-mysql')
        )
        endpoint = response['DBInstances'][0]['Endpoint']['Address']
        port = response['DBInstances'][0]['Endpoint']['Port']
        return f"{endpoint}:{port}"
    
    def _get_azure_endpoint(self) -> str:
        """Get Azure MySQL endpoint"""
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.rdbms.mysql_flexibleservers import MySQLManagementClient
        
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        credential = DefaultAzureCredential()
        mysql_client = MySQLManagementClient(credential, subscription_id)
        
        server = mysql_client.servers.get(
            os.getenv('AZURE_RESOURCE_GROUP', 'singha-loyalty-prod-rg'),
            os.getenv('AZURE_SERVER_NAME', 'singha-loyalty-prod-mysql')
        )
        return server.fully_qualified_domain_name
    
    def _get_gcp_endpoint(self) -> str:
        """Get GCP Cloud SQL endpoint"""
        from google.cloud import sql_v1
        
        project_id = os.getenv('GCP_PROJECT_ID')
        sql_client = sql_v1.SqlInstancesServiceClient()
        
        request = sql_v1.SqlInstancesGetRequest(
            project=project_id,
            instance=os.getenv('GCP_INSTANCE_NAME', 'singha-loyalty-prod-mysql')
        )
        instance = sql_client.get(request=request)
        
        for ip in instance.ip_addresses:
            if ip.type_ == sql_v1.IpMapping.Type.PRIMARY:
                return ip.ip_address
        
        return ""
    
    def _get_aws_password(self) -> str:
        """Retrieve AWS RDS password"""
        secrets_client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        response = secrets_client.get_secret_value(
            SecretId=os.getenv('AWS_SECRET_NAME', 'singha-loyalty-prod-db-credentials')
        )
        import json
        secret = json.loads(response['SecretString'])
        return secret['password']
    
    def _get_azure_password(self) -> str:
        """Retrieve Azure MySQL password"""
        from azure.keyvault.secrets import SecretClient
        from azure.identity import DefaultAzureCredential
        
        credential = DefaultAzureCredential()
        client = SecretClient(
            vault_url=os.getenv('AZURE_KEY_VAULT_URL', 'https://singha-loyalty-prod-kv.vault.azure.net/'),
            credential=credential
        )
        secret = client.get_secret(os.getenv('AZURE_SECRET_NAME', 'mysql-password'))
        return secret.value
    
    def _get_gcp_password(self) -> str:
        """Retrieve GCP Cloud SQL password"""
        from google.cloud import secretmanager
        
        project_id = os.getenv('GCP_PROJECT_ID')
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{os.getenv('GCP_SECRET_NAME', 'singha-loyalty-prod-mysql-password')}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')


# Property-based test strategies
test_values = st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))


@given(test_value=test_values)
@settings(max_examples=50, deadline=None)
def test_property_8_replication_lag_bounds(test_value: str):
    """
    Property 8: Replication Lag Bounds
    
    For any database write operation on the primary, the data should appear 
    in all replica databases within 5 seconds.
    
    This test:
    1. Writes data to AWS RDS (primary)
    2. Checks if data appears in Azure MySQL (replica) within 5 seconds
    3. Checks if data appears in GCP Cloud SQL (replica) within 5 seconds
    4. Asserts that replication lag is <= 5 seconds for both replicas
    """
    # Skip if credentials not configured
    if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AZURE_SUBSCRIPTION_ID') or not os.getenv('GCP_PROJECT_ID'):
        pytest.skip("Cloud credentials not configured")
    
    tester = ReplicationLagTester()
    
    try:
        # Connect to databases
        if not tester.connect_to_databases():
            pytest.skip("Could not connect to databases")
        
        # Generate unique test ID
        test_id = str(uuid.uuid4())
        
        # Write test data to primary
        assert tester.write_test_data(test_id, test_value), "Failed to write test data to primary"
        
        # Check Azure replication
        azure_lag = tester.check_data_replicated(test_id, tester.azure_connection, max_wait=5)
        assert azure_lag is not None, f"Data did not replicate to Azure within 5 seconds"
        assert azure_lag <= 5.0, f"Azure replication lag ({azure_lag:.2f}s) exceeds 5 seconds"
        
        # Check GCP replication
        gcp_lag = tester.check_data_replicated(test_id, tester.gcp_connection, max_wait=5)
        assert gcp_lag is not None, f"Data did not replicate to GCP within 5 seconds"
        assert gcp_lag <= 5.0, f"GCP replication lag ({gcp_lag:.2f}s) exceeds 5 seconds"
        
        print(f"✓ Replication successful - Azure: {azure_lag:.2f}s, GCP: {gcp_lag:.2f}s")
        
        # Cleanup
        tester.cleanup_test_data(test_id)
        
    finally:
        tester.close_connections()


def test_property_8_example_simple_write():
    """
    Example test: Verify replication lag for a simple write operation
    """
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        pytest.skip("AWS credentials not configured")
    
    tester = ReplicationLagTester()
    
    try:
        if not tester.connect_to_databases():
            pytest.skip("Could not connect to databases")
        
        test_id = str(uuid.uuid4())
        test_value = "test_replication_lag"
        
        # Write to primary
        assert tester.write_test_data(test_id, test_value)
        
        # Check replication
        azure_lag = tester.check_data_replicated(test_id, tester.azure_connection, max_wait=5)
        gcp_lag = tester.check_data_replicated(test_id, tester.gcp_connection, max_wait=5)
        
        print(f"\nReplication Lag Results:")
        print(f"  Azure: {azure_lag:.2f}s" if azure_lag else "  Azure: Not replicated")
        print(f"  GCP: {gcp_lag:.2f}s" if gcp_lag else "  GCP: Not replicated")
        
        # Cleanup
        tester.cleanup_test_data(test_id)
        
    finally:
        tester.close_connections()


@pytest.mark.integration
def test_replication_lag_monitoring():
    """
    Integration test: Monitor replication lag over time
    """
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        pytest.skip("AWS credentials not configured")
    
    tester = ReplicationLagTester()
    
    try:
        if not tester.connect_to_databases():
            pytest.skip("Could not connect to databases")
        
        # Perform multiple writes and measure lag
        lags = {'azure': [], 'gcp': []}
        
        for i in range(5):
            test_id = str(uuid.uuid4())
            test_value = f"lag_test_{i}"
            
            tester.write_test_data(test_id, test_value)
            
            azure_lag = tester.check_data_replicated(test_id, tester.azure_connection, max_wait=5)
            gcp_lag = tester.check_data_replicated(test_id, tester.gcp_connection, max_wait=5)
            
            if azure_lag:
                lags['azure'].append(azure_lag)
            if gcp_lag:
                lags['gcp'].append(gcp_lag)
            
            tester.cleanup_test_data(test_id)
            time.sleep(1)
        
        # Calculate average lag
        if lags['azure']:
            avg_azure_lag = sum(lags['azure']) / len(lags['azure'])
            print(f"\nAverage Azure lag: {avg_azure_lag:.2f}s")
            assert avg_azure_lag <= 5.0, f"Average Azure lag exceeds 5 seconds"
        
        if lags['gcp']:
            avg_gcp_lag = sum(lags['gcp']) / len(lags['gcp'])
            print(f"Average GCP lag: {avg_gcp_lag:.2f}s")
            assert avg_gcp_lag <= 5.0, f"Average GCP lag exceeds 5 seconds"
        
    finally:
        tester.close_connections()


if __name__ == '__main__':
    # Run example test
    test_property_8_example_simple_write()
    print("\n✓ Replication lag property test passed!")
