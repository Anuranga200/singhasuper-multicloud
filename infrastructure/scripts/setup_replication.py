#!/usr/bin/env python3
"""
Cross-Cloud Database Replication Setup Script

This script configures binary log replication from AWS RDS MySQL to:
- Azure Database for MySQL Flexible Server
- Google Cloud SQL MySQL

Requirements:
- AWS RDS MySQL 8.0 with binary logging enabled
- Azure Database for MySQL Flexible Server
- Google Cloud SQL MySQL
- Network connectivity between clouds (VPN or public endpoints)
"""

import sys
import time
import logging
from typing import Dict, Optional, Tuple
import boto3
import pymysql
from azure.identity import DefaultAzureCredential
from azure.mgmt.rdbms.mysql_flexibleservers import MySQLManagementClient
from google.cloud import sql_v1
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseReplicationManager:
    """Manages cross-cloud MySQL replication setup"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.aws_rds_endpoint = None
        self.azure_mysql_endpoint = None
        self.gcp_sql_endpoint = None
        
    def setup_aws_primary(self) -> Tuple[bool, str]:
        """
        Configure AWS RDS MySQL as primary with binary logging
        
        Returns:
            Tuple of (success, endpoint)
        """
        logger.info("Setting up AWS RDS as primary database...")
        
        try:
            rds_client = boto3.client('rds', region_name=self.config['aws']['region'])
            
            # Get RDS instance details
            db_identifier = self.config['aws']['db_identifier']
            response = rds_client.describe_db_instances(
                DBInstanceIdentifier=db_identifier
            )
            
            if not response['DBInstances']:
                logger.error(f"RDS instance {db_identifier} not found")
                return False, ""
            
            db_instance = response['DBInstances'][0]
            endpoint = db_instance['Endpoint']['Address']
            port = db_instance['Endpoint']['Port']
            
            logger.info(f"Found RDS instance: {endpoint}:{port}")
            
            # Verify binary logging is enabled
            if not self._verify_binary_logging(endpoint, port):
                logger.error("Binary logging is not enabled on RDS instance")
                return False, ""
            
            # Create replication user
            if not self._create_replication_user(endpoint, port):
                logger.error("Failed to create replication user")
                return False, ""
            
            self.aws_rds_endpoint = f"{endpoint}:{port}"
            logger.info(f"AWS RDS primary configured successfully: {self.aws_rds_endpoint}")
            return True, self.aws_rds_endpoint
            
        except Exception as e:
            logger.error(f"Error setting up AWS RDS primary: {e}")
            return False, ""
    
    def _verify_binary_logging(self, host: str, port: int) -> bool:
        """Verify binary logging is enabled on MySQL"""
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=self.config['aws']['master_username'],
                password=self._get_aws_password(),
                database='mysql'
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW VARIABLES LIKE 'log_bin'")
                result = cursor.fetchone()
                
                if result and result[1] == 'ON':
                    logger.info("Binary logging is enabled")
                    
                    # Get binary log file and position
                    cursor.execute("SHOW MASTER STATUS")
                    master_status = cursor.fetchone()
                    if master_status:
                        logger.info(f"Master log file: {master_status[0]}, Position: {master_status[1]}")
                    
                    connection.close()
                    return True
                else:
                    logger.error("Binary logging is not enabled")
                    connection.close()
                    return False
                    
        except Exception as e:
            logger.error(f"Error verifying binary logging: {e}")
            return False
    
    def _create_replication_user(self, host: str, port: int) -> bool:
        """Create replication user on primary database"""
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=self.config['aws']['master_username'],
                password=self._get_aws_password(),
                database='mysql'
            )
            
            repl_user = self.config['replication']['username']
            repl_pass = self.config['replication']['password']
            
            with connection.cursor() as cursor:
                # Create replication user
                cursor.execute(f"CREATE USER IF NOT EXISTS '{repl_user}'@'%' IDENTIFIED BY '{repl_pass}'")
                cursor.execute(f"GRANT REPLICATION SLAVE ON *.* TO '{repl_user}'@'%'")
                cursor.execute("FLUSH PRIVILEGES")
                
                logger.info(f"Created replication user: {repl_user}")
            
            connection.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating replication user: {e}")
            return False
    
    def setup_azure_replica(self) -> Tuple[bool, str]:
        """
        Configure Azure Database for MySQL as read replica
        
        Returns:
            Tuple of (success, endpoint)
        """
        logger.info("Setting up Azure Database for MySQL as replica...")
        
        try:
            subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
            if not subscription_id:
                logger.error("AZURE_SUBSCRIPTION_ID environment variable not set")
                return False, ""
            
            credential = DefaultAzureCredential()
            mysql_client = MySQLManagementClient(credential, subscription_id)
            
            resource_group = self.config['azure']['resource_group']
            server_name = self.config['azure']['server_name']
            
            # Get Azure MySQL server details
            server = mysql_client.servers.get(resource_group, server_name)
            endpoint = server.fully_qualified_domain_name
            
            logger.info(f"Found Azure MySQL server: {endpoint}")
            
            # Configure replication
            if not self._configure_azure_replication(endpoint):
                logger.error("Failed to configure Azure replication")
                return False, ""
            
            self.azure_mysql_endpoint = endpoint
            logger.info(f"Azure MySQL replica configured successfully: {self.azure_mysql_endpoint}")
            return True, self.azure_mysql_endpoint
            
        except Exception as e:
            logger.error(f"Error setting up Azure replica: {e}")
            return False, ""
    
    def _configure_azure_replication(self, replica_host: str) -> bool:
        """Configure replication on Azure MySQL"""
        try:
            # Connect to Azure MySQL
            connection = pymysql.connect(
                host=replica_host,
                port=3306,
                user=self.config['azure']['admin_username'],
                password=self._get_azure_password(),
                database='mysql'
            )
            
            # Get master status from AWS
            master_host = self.aws_rds_endpoint.split(':')[0]
            master_port = int(self.aws_rds_endpoint.split(':')[1])
            
            master_conn = pymysql.connect(
                host=master_host,
                port=master_port,
                user=self.config['aws']['master_username'],
                password=self._get_aws_password(),
                database='mysql'
            )
            
            with master_conn.cursor() as cursor:
                cursor.execute("SHOW MASTER STATUS")
                master_status = cursor.fetchone()
                log_file = master_status[0]
                log_pos = master_status[1]
            
            master_conn.close()
            
            # Configure replica
            with connection.cursor() as cursor:
                # Stop replica if running
                cursor.execute("STOP REPLICA")
                
                # Configure master connection
                repl_user = self.config['replication']['username']
                repl_pass = self.config['replication']['password']
                
                change_master_sql = f"""
                CHANGE MASTER TO
                    MASTER_HOST='{master_host}',
                    MASTER_PORT={master_port},
                    MASTER_USER='{repl_user}',
                    MASTER_PASSWORD='{repl_pass}',
                    MASTER_LOG_FILE='{log_file}',
                    MASTER_LOG_POS={log_pos},
                    MASTER_SSL=1
                """
                cursor.execute(change_master_sql)
                
                # Start replica
                cursor.execute("START REPLICA")
                
                # Check replica status
                time.sleep(2)
                cursor.execute("SHOW REPLICA STATUS")
                replica_status = cursor.fetchone()
                
                if replica_status:
                    logger.info("Azure replication started successfully")
                    logger.info(f"Replica IO Running: {replica_status[10]}")
                    logger.info(f"Replica SQL Running: {replica_status[11]}")
                else:
                    logger.error("Failed to get replica status")
                    connection.close()
                    return False
            
            connection.close()
            return True
            
        except Exception as e:
            logger.error(f"Error configuring Azure replication: {e}")
            return False
    
    def setup_gcp_replica(self) -> Tuple[bool, str]:
        """
        Configure Google Cloud SQL MySQL as read replica
        
        Returns:
            Tuple of (success, endpoint)
        """
        logger.info("Setting up Google Cloud SQL as replica...")
        
        try:
            project_id = os.getenv('GCP_PROJECT_ID')
            if not project_id:
                logger.error("GCP_PROJECT_ID environment variable not set")
                return False, ""
            
            sql_client = sql_v1.SqlInstancesServiceClient()
            
            instance_name = self.config['gcp']['instance_name']
            
            # Get Cloud SQL instance details
            request = sql_v1.SqlInstancesGetRequest(
                project=project_id,
                instance=instance_name
            )
            instance = sql_client.get(request=request)
            
            # Get IP address
            endpoint = None
            for ip in instance.ip_addresses:
                if ip.type_ == sql_v1.IpMapping.Type.PRIMARY:
                    endpoint = ip.ip_address
                    break
            
            if not endpoint:
                logger.error("Could not find Cloud SQL IP address")
                return False, ""
            
            logger.info(f"Found Cloud SQL instance: {endpoint}")
            
            # Configure replication
            if not self._configure_gcp_replication(endpoint):
                logger.error("Failed to configure GCP replication")
                return False, ""
            
            self.gcp_sql_endpoint = endpoint
            logger.info(f"GCP Cloud SQL replica configured successfully: {self.gcp_sql_endpoint}")
            return True, self.gcp_sql_endpoint
            
        except Exception as e:
            logger.error(f"Error setting up GCP replica: {e}")
            return False, ""
    
    def _configure_gcp_replication(self, replica_host: str) -> bool:
        """Configure replication on GCP Cloud SQL"""
        try:
            # Connect to Cloud SQL
            connection = pymysql.connect(
                host=replica_host,
                port=3306,
                user=self.config['gcp']['root_username'],
                password=self._get_gcp_password(),
                database='mysql'
            )
            
            # Get master status from AWS
            master_host = self.aws_rds_endpoint.split(':')[0]
            master_port = int(self.aws_rds_endpoint.split(':')[1])
            
            master_conn = pymysql.connect(
                host=master_host,
                port=master_port,
                user=self.config['aws']['master_username'],
                password=self._get_aws_password(),
                database='mysql'
            )
            
            with master_conn.cursor() as cursor:
                cursor.execute("SHOW MASTER STATUS")
                master_status = cursor.fetchone()
                log_file = master_status[0]
                log_pos = master_status[1]
            
            master_conn.close()
            
            # Configure replica
            with connection.cursor() as cursor:
                # Stop replica if running
                cursor.execute("STOP REPLICA")
                
                # Configure master connection
                repl_user = self.config['replication']['username']
                repl_pass = self.config['replication']['password']
                
                change_master_sql = f"""
                CHANGE MASTER TO
                    MASTER_HOST='{master_host}',
                    MASTER_PORT={master_port},
                    MASTER_USER='{repl_user}',
                    MASTER_PASSWORD='{repl_pass}',
                    MASTER_LOG_FILE='{log_file}',
                    MASTER_LOG_POS={log_pos},
                    MASTER_SSL=1
                """
                cursor.execute(change_master_sql)
                
                # Start replica
                cursor.execute("START REPLICA")
                
                # Check replica status
                time.sleep(2)
                cursor.execute("SHOW REPLICA STATUS")
                replica_status = cursor.fetchone()
                
                if replica_status:
                    logger.info("GCP replication started successfully")
                    logger.info(f"Replica IO Running: {replica_status[10]}")
                    logger.info(f"Replica SQL Running: {replica_status[11]}")
                else:
                    logger.error("Failed to get replica status")
                    connection.close()
                    return False
            
            connection.close()
            return True
            
        except Exception as e:
            logger.error(f"Error configuring GCP replication: {e}")
            return False
    
    def monitor_replication_lag(self) -> Dict[str, Optional[float]]:
        """
        Monitor replication lag on all replicas
        
        Returns:
            Dictionary with lag in seconds for each replica
        """
        logger.info("Monitoring replication lag...")
        
        lag_data = {
            'azure': None,
            'gcp': None
        }
        
        # Check Azure lag
        if self.azure_mysql_endpoint:
            lag_data['azure'] = self._get_replication_lag(
                self.azure_mysql_endpoint,
                self.config['azure']['admin_username'],
                self._get_azure_password()
            )
        
        # Check GCP lag
        if self.gcp_sql_endpoint:
            lag_data['gcp'] = self._get_replication_lag(
                self.gcp_sql_endpoint,
                self.config['gcp']['root_username'],
                self._get_gcp_password()
            )
        
        return lag_data
    
    def _get_replication_lag(self, host: str, user: str, password: str) -> Optional[float]:
        """Get replication lag in seconds for a replica"""
        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database='mysql'
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW REPLICA STATUS")
                replica_status = cursor.fetchone()
                
                if replica_status:
                    # Seconds_Behind_Master is at index 32
                    lag = replica_status[32]
                    if lag is not None:
                        logger.info(f"Replication lag for {host}: {lag} seconds")
                        return float(lag)
                    else:
                        logger.warning(f"Replication lag is NULL for {host}")
                        return None
                else:
                    logger.error(f"Could not get replica status for {host}")
                    return None
            
            connection.close()
            
        except Exception as e:
            logger.error(f"Error getting replication lag for {host}: {e}")
            return None
    
    def _get_aws_password(self) -> str:
        """Retrieve AWS RDS password from Secrets Manager"""
        try:
            secrets_client = boto3.client('secretsmanager', region_name=self.config['aws']['region'])
            secret_name = self.config['aws']['secret_name']
            
            response = secrets_client.get_secret_value(SecretId=secret_name)
            import json
            secret = json.loads(response['SecretString'])
            return secret['password']
            
        except Exception as e:
            logger.error(f"Error retrieving AWS password: {e}")
            return ""
    
    def _get_azure_password(self) -> str:
        """Retrieve Azure MySQL password from Key Vault"""
        try:
            from azure.keyvault.secrets import SecretClient
            
            credential = DefaultAzureCredential()
            vault_url = self.config['azure']['key_vault_url']
            secret_name = self.config['azure']['secret_name']
            
            client = SecretClient(vault_url=vault_url, credential=credential)
            secret = client.get_secret(secret_name)
            return secret.value
            
        except Exception as e:
            logger.error(f"Error retrieving Azure password: {e}")
            return ""
    
    def _get_gcp_password(self) -> str:
        """Retrieve GCP Cloud SQL password from Secret Manager"""
        try:
            from google.cloud import secretmanager
            
            project_id = os.getenv('GCP_PROJECT_ID')
            secret_name = self.config['gcp']['secret_name']
            
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
            
        except Exception as e:
            logger.error(f"Error retrieving GCP password: {e}")
            return ""


def load_config() -> Dict:
    """Load configuration from environment variables or config file"""
    return {
        'aws': {
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'db_identifier': os.getenv('AWS_DB_IDENTIFIER', 'singha-loyalty-prod-mysql'),
            'master_username': os.getenv('AWS_MASTER_USERNAME', 'admin'),
            'secret_name': os.getenv('AWS_SECRET_NAME', 'singha-loyalty-prod-db-credentials')
        },
        'azure': {
            'resource_group': os.getenv('AZURE_RESOURCE_GROUP', 'singha-loyalty-prod-rg'),
            'server_name': os.getenv('AZURE_SERVER_NAME', 'singha-loyalty-prod-mysql'),
            'admin_username': os.getenv('AZURE_ADMIN_USERNAME', 'azureadmin'),
            'key_vault_url': os.getenv('AZURE_KEY_VAULT_URL', 'https://singha-loyalty-prod-kv.vault.azure.net/'),
            'secret_name': os.getenv('AZURE_SECRET_NAME', 'mysql-password')
        },
        'gcp': {
            'instance_name': os.getenv('GCP_INSTANCE_NAME', 'singha-loyalty-prod-mysql'),
            'root_username': os.getenv('GCP_ROOT_USERNAME', 'root'),
            'secret_name': os.getenv('GCP_SECRET_NAME', 'singha-loyalty-prod-mysql-password')
        },
        'replication': {
            'username': os.getenv('REPLICATION_USERNAME', 'repl_user'),
            'password': os.getenv('REPLICATION_PASSWORD', 'change_me_in_production')
        }
    }


def main():
    """Main execution flow"""
    logger.info("Starting cross-cloud database replication setup...")
    
    config = load_config()
    manager = DatabaseReplicationManager(config)
    
    # Step 1: Setup AWS as primary
    success, endpoint = manager.setup_aws_primary()
    if not success:
        logger.error("Failed to setup AWS primary. Exiting.")
        sys.exit(1)
    
    # Step 2: Setup Azure replica
    success, endpoint = manager.setup_azure_replica()
    if not success:
        logger.error("Failed to setup Azure replica. Continuing with GCP...")
    
    # Step 3: Setup GCP replica
    success, endpoint = manager.setup_gcp_replica()
    if not success:
        logger.error("Failed to setup GCP replica.")
    
    # Step 4: Monitor replication lag
    logger.info("\nMonitoring replication lag...")
    lag_data = manager.monitor_replication_lag()
    
    print("\n" + "="*60)
    print("REPLICATION SETUP SUMMARY")
    print("="*60)
    print(f"AWS Primary: {manager.aws_rds_endpoint}")
    print(f"Azure Replica: {manager.azure_mysql_endpoint}")
    print(f"GCP Replica: {manager.gcp_sql_endpoint}")
    print("\nReplication Lag:")
    print(f"  Azure: {lag_data['azure']} seconds" if lag_data['azure'] is not None else "  Azure: Not available")
    print(f"  GCP: {lag_data['gcp']} seconds" if lag_data['gcp'] is not None else "  GCP: Not available")
    print("="*60)
    
    logger.info("Replication setup completed!")


if __name__ == '__main__':
    main()
