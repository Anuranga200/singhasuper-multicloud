#!/usr/bin/env python3
"""
Database Consistency Verification Script

This script verifies data consistency across AWS, Azure, and GCP MySQL databases by:
- Comparing row counts for all tables
- Computing and comparing checksums for table data
- Identifying discrepancies between primary and replicas
- Logging inconsistencies for investigation

Requirements:
- Access to AWS RDS MySQL
- Access to Azure Database for MySQL
- Access to Google Cloud SQL MySQL
"""

import sys
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import boto3
import pymysql
from azure.identity import DefaultAzureCredential
from azure.mgmt.rdbms.mysql_flexibleservers import MySQLManagementClient
from google.cloud import sql_v1
import os
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TableStats:
    """Statistics for a database table"""
    table_name: str
    row_count: int
    checksum: str
    last_updated: Optional[datetime] = None


@dataclass
class ConsistencyReport:
    """Report of consistency check results"""
    timestamp: datetime
    consistent: bool
    aws_tables: Dict[str, TableStats]
    azure_tables: Dict[str, TableStats]
    gcp_tables: Dict[str, TableStats]
    discrepancies: List[str]


class DatabaseConsistencyChecker:
    """Checks data consistency across multi-cloud databases"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.aws_connection = None
        self.azure_connection = None
        self.gcp_connection = None
        
    def connect_to_databases(self) -> bool:
        """Establish connections to all databases"""
        logger.info("Connecting to databases...")
        
        # Connect to AWS RDS
        try:
            aws_endpoint = self._get_aws_endpoint()
            self.aws_connection = pymysql.connect(
                host=aws_endpoint.split(':')[0],
                port=int(aws_endpoint.split(':')[1]) if ':' in aws_endpoint else 3306,
                user=self.config['aws']['master_username'],
                password=self._get_aws_password(),
                database=self.config['database_name']
            )
            logger.info("Connected to AWS RDS")
        except Exception as e:
            logger.error(f"Failed to connect to AWS RDS: {e}")
            return False
        
        # Connect to Azure MySQL
        try:
            azure_endpoint = self._get_azure_endpoint()
            self.azure_connection = pymysql.connect(
                host=azure_endpoint,
                port=3306,
                user=self.config['azure']['admin_username'],
                password=self._get_azure_password(),
                database=self.config['database_name']
            )
            logger.info("Connected to Azure MySQL")
        except Exception as e:
            logger.error(f"Failed to connect to Azure MySQL: {e}")
            return False
        
        # Connect to GCP Cloud SQL
        try:
            gcp_endpoint = self._get_gcp_endpoint()
            self.gcp_connection = pymysql.connect(
                host=gcp_endpoint,
                port=3306,
                user=self.config['gcp']['root_username'],
                password=self._get_gcp_password(),
                database=self.config['database_name']
            )
            logger.info("Connected to GCP Cloud SQL")
        except Exception as e:
            logger.error(f"Failed to connect to GCP Cloud SQL: {e}")
            return False
        
        return True
    
    def get_table_list(self, connection) -> List[str]:
        """Get list of all tables in database"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
        except Exception as e:
            logger.error(f"Error getting table list: {e}")
            return []
    
    def get_table_stats(self, connection, table_name: str) -> Optional[TableStats]:
        """Get statistics for a specific table"""
        try:
            with connection.cursor() as cursor:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                row_count = cursor.fetchone()[0]
                
                # Get checksum (using MD5 of concatenated column values)
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = [row[0] for row in cursor.fetchall()]
                
                # Build checksum query
                column_concat = ", ".join([f"COALESCE(CAST(`{col}` AS CHAR), 'NULL')" for col in columns])
                checksum_query = f"""
                    SELECT MD5(GROUP_CONCAT(row_hash ORDER BY row_hash SEPARATOR ''))
                    FROM (
                        SELECT MD5(CONCAT({column_concat})) as row_hash
                        FROM `{table_name}`
                        ORDER BY {columns[0]}
                        LIMIT 10000
                    ) as hashes
                """
                
                cursor.execute(checksum_query)
                checksum = cursor.fetchone()[0] or "empty"
                
                return TableStats(
                    table_name=table_name,
                    row_count=row_count,
                    checksum=checksum,
                    last_updated=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error getting stats for table {table_name}: {e}")
            return None
    
    def verify_consistency(self) -> ConsistencyReport:
        """Verify consistency across all databases"""
        logger.info("Starting consistency verification...")
        
        discrepancies = []
        
        # Get table lists
        aws_tables_list = self.get_table_list(self.aws_connection)
        azure_tables_list = self.get_table_list(self.azure_connection)
        gcp_tables_list = self.get_table_list(self.gcp_connection)
        
        logger.info(f"Found {len(aws_tables_list)} tables in AWS")
        logger.info(f"Found {len(azure_tables_list)} tables in Azure")
        logger.info(f"Found {len(gcp_tables_list)} tables in GCP")
        
        # Check if table lists match
        if set(aws_tables_list) != set(azure_tables_list):
            discrepancy = "Table list mismatch between AWS and Azure"
            discrepancies.append(discrepancy)
            logger.warning(discrepancy)
        
        if set(aws_tables_list) != set(gcp_tables_list):
            discrepancy = "Table list mismatch between AWS and GCP"
            discrepancies.append(discrepancy)
            logger.warning(discrepancy)
        
        # Get stats for all tables
        aws_tables = {}
        azure_tables = {}
        gcp_tables = {}
        
        all_tables = set(aws_tables_list + azure_tables_list + gcp_tables_list)
        
        for table_name in all_tables:
            logger.info(f"Checking table: {table_name}")
            
            # Get AWS stats
            if table_name in aws_tables_list:
                aws_stats = self.get_table_stats(self.aws_connection, table_name)
                if aws_stats:
                    aws_tables[table_name] = aws_stats
            
            # Get Azure stats
            if table_name in azure_tables_list:
                azure_stats = self.get_table_stats(self.azure_connection, table_name)
                if azure_stats:
                    azure_tables[table_name] = azure_stats
            
            # Get GCP stats
            if table_name in gcp_tables_list:
                gcp_stats = self.get_table_stats(self.gcp_connection, table_name)
                if gcp_stats:
                    gcp_tables[table_name] = gcp_stats
            
            # Compare stats
            if table_name in aws_tables and table_name in azure_tables:
                if aws_tables[table_name].row_count != azure_tables[table_name].row_count:
                    discrepancy = f"Row count mismatch for {table_name}: AWS={aws_tables[table_name].row_count}, Azure={azure_tables[table_name].row_count}"
                    discrepancies.append(discrepancy)
                    logger.warning(discrepancy)
                
                if aws_tables[table_name].checksum != azure_tables[table_name].checksum:
                    discrepancy = f"Checksum mismatch for {table_name}: AWS={aws_tables[table_name].checksum}, Azure={azure_tables[table_name].checksum}"
                    discrepancies.append(discrepancy)
                    logger.warning(discrepancy)
            
            if table_name in aws_tables and table_name in gcp_tables:
                if aws_tables[table_name].row_count != gcp_tables[table_name].row_count:
                    discrepancy = f"Row count mismatch for {table_name}: AWS={aws_tables[table_name].row_count}, GCP={gcp_tables[table_name].row_count}"
                    discrepancies.append(discrepancy)
                    logger.warning(discrepancy)
                
                if aws_tables[table_name].checksum != gcp_tables[table_name].checksum:
                    discrepancy = f"Checksum mismatch for {table_name}: AWS={aws_tables[table_name].checksum}, GCP={gcp_tables[table_name].checksum}"
                    discrepancies.append(discrepancy)
                    logger.warning(discrepancy)
        
        # Create report
        report = ConsistencyReport(
            timestamp=datetime.now(),
            consistent=len(discrepancies) == 0,
            aws_tables=aws_tables,
            azure_tables=azure_tables,
            gcp_tables=gcp_tables,
            discrepancies=discrepancies
        )
        
        return report
    
    def print_report(self, report: ConsistencyReport):
        """Print consistency report"""
        print("\n" + "="*80)
        print("DATABASE CONSISTENCY REPORT")
        print("="*80)
        print(f"Timestamp: {report.timestamp}")
        print(f"Status: {'✓ CONSISTENT' if report.consistent else '✗ INCONSISTENT'}")
        print(f"\nTables Checked:")
        print(f"  AWS: {len(report.aws_tables)} tables")
        print(f"  Azure: {len(report.azure_tables)} tables")
        print(f"  GCP: {len(report.gcp_tables)} tables")
        
        if report.discrepancies:
            print(f"\n⚠ Found {len(report.discrepancies)} discrepancies:")
            for i, discrepancy in enumerate(report.discrepancies, 1):
                print(f"  {i}. {discrepancy}")
        else:
            print("\n✓ All databases are consistent!")
        
        print("\nTable Details:")
        all_tables = set(list(report.aws_tables.keys()) + list(report.azure_tables.keys()) + list(report.gcp_tables.keys()))
        
        for table_name in sorted(all_tables):
            print(f"\n  Table: {table_name}")
            
            if table_name in report.aws_tables:
                stats = report.aws_tables[table_name]
                print(f"    AWS:   {stats.row_count:,} rows, checksum={stats.checksum[:8]}...")
            
            if table_name in report.azure_tables:
                stats = report.azure_tables[table_name]
                print(f"    Azure: {stats.row_count:,} rows, checksum={stats.checksum[:8]}...")
            
            if table_name in report.gcp_tables:
                stats = report.gcp_tables[table_name]
                print(f"    GCP:   {stats.row_count:,} rows, checksum={stats.checksum[:8]}...")
        
        print("="*80 + "\n")
    
    def save_report(self, report: ConsistencyReport, filename: str = "consistency_report.log"):
        """Save consistency report to file"""
        try:
            with open(filename, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Consistency Check: {report.timestamp}\n")
                f.write(f"Status: {'CONSISTENT' if report.consistent else 'INCONSISTENT'}\n")
                f.write(f"Discrepancies: {len(report.discrepancies)}\n")
                
                if report.discrepancies:
                    f.write("\nDiscrepancies:\n")
                    for discrepancy in report.discrepancies:
                        f.write(f"  - {discrepancy}\n")
                
                f.write(f"{'='*80}\n")
            
            logger.info(f"Report saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    
    def close_connections(self):
        """Close all database connections"""
        if self.aws_connection:
            self.aws_connection.close()
            logger.info("Closed AWS connection")
        
        if self.azure_connection:
            self.azure_connection.close()
            logger.info("Closed Azure connection")
        
        if self.gcp_connection:
            self.gcp_connection.close()
            logger.info("Closed GCP connection")
    
    def _get_aws_endpoint(self) -> str:
        """Get AWS RDS endpoint"""
        try:
            rds_client = boto3.client('rds', region_name=self.config['aws']['region'])
            response = rds_client.describe_db_instances(
                DBInstanceIdentifier=self.config['aws']['db_identifier']
            )
            endpoint = response['DBInstances'][0]['Endpoint']['Address']
            port = response['DBInstances'][0]['Endpoint']['Port']
            return f"{endpoint}:{port}"
        except Exception as e:
            logger.error(f"Error getting AWS endpoint: {e}")
            return ""
    
    def _get_azure_endpoint(self) -> str:
        """Get Azure MySQL endpoint"""
        try:
            subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
            credential = DefaultAzureCredential()
            mysql_client = MySQLManagementClient(credential, subscription_id)
            
            server = mysql_client.servers.get(
                self.config['azure']['resource_group'],
                self.config['azure']['server_name']
            )
            return server.fully_qualified_domain_name
        except Exception as e:
            logger.error(f"Error getting Azure endpoint: {e}")
            return ""
    
    def _get_gcp_endpoint(self) -> str:
        """Get GCP Cloud SQL endpoint"""
        try:
            project_id = os.getenv('GCP_PROJECT_ID')
            sql_client = sql_v1.SqlInstancesServiceClient()
            
            request = sql_v1.SqlInstancesGetRequest(
                project=project_id,
                instance=self.config['gcp']['instance_name']
            )
            instance = sql_client.get(request=request)
            
            for ip in instance.ip_addresses:
                if ip.type_ == sql_v1.IpMapping.Type.PRIMARY:
                    return ip.ip_address
            
            return ""
        except Exception as e:
            logger.error(f"Error getting GCP endpoint: {e}")
            return ""
    
    def _get_aws_password(self) -> str:
        """Retrieve AWS RDS password from Secrets Manager"""
        try:
            secrets_client = boto3.client('secretsmanager', region_name=self.config['aws']['region'])
            response = secrets_client.get_secret_value(SecretId=self.config['aws']['secret_name'])
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
            client = SecretClient(vault_url=self.config['azure']['key_vault_url'], credential=credential)
            secret = client.get_secret(self.config['azure']['secret_name'])
            return secret.value
        except Exception as e:
            logger.error(f"Error retrieving Azure password: {e}")
            return ""
    
    def _get_gcp_password(self) -> str:
        """Retrieve GCP Cloud SQL password from Secret Manager"""
        try:
            from google.cloud import secretmanager
            project_id = os.getenv('GCP_PROJECT_ID')
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{self.config['gcp']['secret_name']}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.error(f"Error retrieving GCP password: {e}")
            return ""


def load_config() -> Dict:
    """Load configuration from environment variables"""
    return {
        'database_name': os.getenv('DATABASE_NAME', 'singha_loyalty'),
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
        }
    }


def main():
    """Main execution flow"""
    logger.info("Starting database consistency verification...")
    
    config = load_config()
    checker = DatabaseConsistencyChecker(config)
    
    try:
        # Connect to databases
        if not checker.connect_to_databases():
            logger.error("Failed to connect to databases. Exiting.")
            sys.exit(1)
        
        # Verify consistency
        report = checker.verify_consistency()
        
        # Print report
        checker.print_report(report)
        
        # Save report
        checker.save_report(report)
        
        # Exit with appropriate code
        if report.consistent:
            logger.info("✓ Consistency check passed!")
            sys.exit(0)
        else:
            logger.error("✗ Consistency check failed!")
            sys.exit(1)
            
    finally:
        checker.close_connections()


if __name__ == '__main__':
    main()
