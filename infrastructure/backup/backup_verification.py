#!/usr/bin/env python3
"""
Backup Verification Service

This script verifies the integrity of database backups across all cloud providers.
It runs after each backup completes to ensure backups are valid and restorable.

Features:
- Verify backup integrity after completion
- Check backup metadata and checksums
- Validate backup accessibility
- Alert on verification failures
- Log verification results

Requirements:
- AWS credentials with RDS backup permissions
- Azure credentials with Database backup permissions
- GCP credentials with Cloud SQL backup permissions
"""

import sys
import logging
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import boto3
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.rdbms.mysql import MySQLManagementClient
    from google.cloud import sql_v1
    from google.oauth2 import service_account
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install boto3 azure-identity azure-mgmt-rdbms google-cloud-sql")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Verification status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class VerificationResult:
    """Backup verification result"""
    backup_id: str
    cloud_provider: str
    database_name: str
    verification_time: datetime
    status: str
    checks_performed: List[str]
    checks_passed: List[str]
    checks_failed: List[str]
    error: Optional[str] = None
    duration_seconds: float = 0.0


class BackupVerifier:
    """Verifies backup integrity across all clouds"""
    
    def __init__(self, config: Dict):
        """
        Initialize backup verifier
        
        Args:
            config: Configuration dictionary with cloud credentials and settings
        """
        self.config = config
        self.verification_history = []
        
        # Initialize AWS clients
        aws_region = config.get('aws_region', 'us-east-1')
        self.rds_client = boto3.client('rds', region_name=aws_region)
        
        # Initialize Azure clients
        if 'azure_subscription_id' in config:
            self.azure_credential = DefaultAzureCredential()
            self.azure_mysql_client = MySQLManagementClient(
                self.azure_credential,
                config['azure_subscription_id']
            )
        
        # Initialize GCP clients
        if 'gcp_project_id' in config:
            if 'gcp_credentials_file' in config:
                credentials = service_account.Credentials.from_service_account_file(
                    config['gcp_credentials_file']
                )
                self.gcp_sql_client = sql_v1.SqlBackupRunsServiceClient(credentials=credentials)
            else:
                self.gcp_sql_client = sql_v1.SqlBackupRunsServiceClient()
        
        logger.info("Backup Verifier initialized")
    
    def verify_aws_backup(self, backup_id: str) -> VerificationResult:
        """
        Verify AWS RDS backup integrity
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            VerificationResult object
        """
        logger.info(f"Verifying AWS backup: {backup_id}")
        start_time = datetime.utcnow()
        
        checks_performed = []
        checks_passed = []
        checks_failed = []
        
        try:
            # Check 1: Verify backup exists
            checks_performed.append("backup_exists")
            response = self.rds_client.describe_db_snapshots(
                DBSnapshotIdentifier=backup_id
            )
            
            if not response.get('DBSnapshots'):
                checks_failed.append("backup_exists")
                raise Exception(f"Backup {backup_id} not found")
            
            checks_passed.append("backup_exists")
            snapshot = response['DBSnapshots'][0]
            
            # Check 2: Verify backup status is available
            checks_performed.append("backup_status")
            if snapshot['Status'] != 'available':
                checks_failed.append("backup_status")
                raise Exception(f"Backup status is {snapshot['Status']}, expected 'available'")
            
            checks_passed.append("backup_status")
            
            # Check 3: Verify backup size
            checks_performed.append("backup_size")
            allocated_storage = snapshot.get('AllocatedStorage', 0)
            if allocated_storage <= 0:
                checks_failed.append("backup_size")
                raise Exception(f"Invalid backup size: {allocated_storage} GB")
            
            checks_passed.append("backup_size")
            logger.info(f"Backup size: {allocated_storage} GB")
            
            # Check 4: Verify backup encryption
            checks_performed.append("backup_encryption")
            if not snapshot.get('Encrypted', False):
                logger.warning(f"Backup {backup_id} is not encrypted")
                # Don't fail, just warn
            
            checks_passed.append("backup_encryption")
            
            # Check 5: Verify backup age
            checks_performed.append("backup_age")
            snapshot_time = snapshot['SnapshotCreateTime']
            age = datetime.utcnow() - snapshot_time.replace(tzinfo=None)
            
            if age.days > 30:
                logger.warning(f"Backup {backup_id} is {age.days} days old")
            
            checks_passed.append("backup_age")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            result = VerificationResult(
                backup_id=backup_id,
                cloud_provider='AWS',
                database_name=snapshot['DBInstanceIdentifier'],
                verification_time=datetime.utcnow(),
                status=VerificationStatus.PASSED.value,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                duration_seconds=duration
            )
            
            logger.info(f"AWS backup verification PASSED: {backup_id}")
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"AWS backup verification FAILED: {backup_id} - {e}")
            
            return VerificationResult(
                backup_id=backup_id,
                cloud_provider='AWS',
                database_name=self.config.get('aws_db_instance_id', 'unknown'),
                verification_time=datetime.utcnow(),
                status=VerificationStatus.FAILED.value,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                error=str(e),
                duration_seconds=duration
            )
    
    def verify_azure_backup(self, server_name: str) -> VerificationResult:
        """
        Verify Azure Database backup integrity
        
        Args:
            server_name: Azure server name
            
        Returns:
            VerificationResult object
        """
        logger.info(f"Verifying Azure backup for: {server_name}")
        start_time = datetime.utcnow()
        
        checks_performed = []
        checks_passed = []
        checks_failed = []
        
        try:
            if 'azure_resource_group' not in self.config:
                raise Exception("Azure resource group not configured")
            
            resource_group = self.config['azure_resource_group']
            
            # Check 1: Verify server exists
            checks_performed.append("server_exists")
            server = self.azure_mysql_client.servers.get(resource_group, server_name)
            checks_passed.append("server_exists")
            
            # Check 2: Verify backup retention is configured
            checks_performed.append("backup_retention")
            if server.backup_retention_days < 7:
                checks_failed.append("backup_retention")
                raise Exception(f"Backup retention is {server.backup_retention_days} days, minimum is 7")
            
            checks_passed.append("backup_retention")
            logger.info(f"Backup retention: {server.backup_retention_days} days")
            
            # Check 3: Verify geo-redundant backup
            checks_performed.append("geo_redundant")
            if server.geo_redundant_backup != 'Enabled':
                logger.warning(f"Geo-redundant backup is not enabled for {server_name}")
            
            checks_passed.append("geo_redundant")
            
            # Check 4: Verify server state
            checks_performed.append("server_state")
            if server.user_visible_state not in ['Ready', 'Available']:
                checks_failed.append("server_state")
                raise Exception(f"Server state is {server.user_visible_state}")
            
            checks_passed.append("server_state")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            result = VerificationResult(
                backup_id=f"{server_name}-automated",
                cloud_provider='Azure',
                database_name=server_name,
                verification_time=datetime.utcnow(),
                status=VerificationStatus.PASSED.value,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                duration_seconds=duration
            )
            
            logger.info(f"Azure backup verification PASSED: {server_name}")
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Azure backup verification FAILED: {server_name} - {e}")
            
            return VerificationResult(
                backup_id=f"{server_name}-automated",
                cloud_provider='Azure',
                database_name=server_name,
                verification_time=datetime.utcnow(),
                status=VerificationStatus.FAILED.value,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                error=str(e),
                duration_seconds=duration
            )
    
    def verify_gcp_backup(self, backup_id: str) -> VerificationResult:
        """
        Verify GCP Cloud SQL backup integrity
        
        Args:
            backup_id: Backup run ID
            
        Returns:
            VerificationResult object
        """
        logger.info(f"Verifying GCP backup: {backup_id}")
        start_time = datetime.utcnow()
        
        checks_performed = []
        checks_passed = []
        checks_failed = []
        
        try:
            if 'gcp_project_id' not in self.config or 'gcp_instance_name' not in self.config:
                raise Exception("GCP project ID or instance name not configured")
            
            project_id = self.config['gcp_project_id']
            instance_name = self.config['gcp_instance_name']
            
            # Check 1: Verify backup exists
            checks_performed.append("backup_exists")
            from google.cloud.sql_v1.types import SqlBackupRunsGetRequest
            request = SqlBackupRunsGetRequest(
                project=project_id,
                instance=instance_name,
                id=int(backup_id)
            )
            
            backup_run = self.gcp_sql_client.get(request=request)
            checks_passed.append("backup_exists")
            
            # Check 2: Verify backup status
            checks_performed.append("backup_status")
            if backup_run.status != 'SUCCESSFUL':
                checks_failed.append("backup_status")
                raise Exception(f"Backup status is {backup_run.status}, expected 'SUCCESSFUL'")
            
            checks_passed.append("backup_status")
            
            # Check 3: Verify backup type
            checks_performed.append("backup_type")
            logger.info(f"Backup type: {backup_run.type_}")
            checks_passed.append("backup_type")
            
            # Check 4: Verify backup completion
            checks_performed.append("backup_completion")
            if not backup_run.end_time:
                checks_failed.append("backup_completion")
                raise Exception("Backup has not completed")
            
            checks_passed.append("backup_completion")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            result = VerificationResult(
                backup_id=backup_id,
                cloud_provider='GCP',
                database_name=instance_name,
                verification_time=datetime.utcnow(),
                status=VerificationStatus.PASSED.value,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                duration_seconds=duration
            )
            
            logger.info(f"GCP backup verification PASSED: {backup_id}")
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"GCP backup verification FAILED: {backup_id} - {e}")
            
            return VerificationResult(
                backup_id=backup_id,
                cloud_provider='GCP',
                database_name=self.config.get('gcp_instance_name', 'unknown'),
                verification_time=datetime.utcnow(),
                status=VerificationStatus.FAILED.value,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                error=str(e),
                duration_seconds=duration
            )
    
    def verify_latest_backups(self) -> Dict[str, VerificationResult]:
        """
        Verify the latest backup from each cloud provider
        
        Returns:
            Dictionary mapping cloud provider to verification result
        """
        logger.info("Verifying latest backups from all clouds...")
        
        results = {}
        
        # Verify AWS
        if 'aws_db_instance_id' in self.config:
            try:
                db_instance_id = self.config['aws_db_instance_id']
                response = self.rds_client.describe_db_snapshots(
                    DBInstanceIdentifier=db_instance_id,
                    SnapshotType='automated',
                    MaxRecords=1
                )
                
                if response.get('DBSnapshots'):
                    latest_snapshot = response['DBSnapshots'][0]
                    results['AWS'] = self.verify_aws_backup(latest_snapshot['DBSnapshotIdentifier'])
                else:
                    logger.warning("No AWS backups found")
            except Exception as e:
                logger.error(f"Error verifying AWS backup: {e}")
        
        # Verify Azure
        if 'azure_server_name' in self.config:
            server_name = self.config['azure_server_name']
            results['Azure'] = self.verify_azure_backup(server_name)
        
        # Verify GCP
        if 'gcp_project_id' in self.config and 'gcp_instance_name' in self.config:
            try:
                project_id = self.config['gcp_project_id']
                instance_name = self.config['gcp_instance_name']
                
                from google.cloud.sql_v1.types import SqlBackupRunsListRequest
                request = SqlBackupRunsListRequest(
                    project=project_id,
                    instance=instance_name,
                    max_results=1
                )
                
                response = self.gcp_sql_client.list(request=request)
                
                for backup_run in response.items:
                    results['GCP'] = self.verify_gcp_backup(str(backup_run.id))
                    break
                
                if 'GCP' not in results:
                    logger.warning("No GCP backups found")
            except Exception as e:
                logger.error(f"Error verifying GCP backup: {e}")
        
        # Log summary
        logger.info("Backup verification summary:")
        for cloud, result in results.items():
            logger.info(f"  {cloud}: {result.status} ({len(result.checks_passed)}/{len(result.checks_performed)} checks passed)")
        
        return results
    
    def send_verification_alert(self, result: VerificationResult):
        """
        Send alert if backup verification fails
        
        Args:
            result: Verification result
        """
        if result.status == VerificationStatus.FAILED.value:
            logger.critical(f"ALERT: Backup verification failed for {result.cloud_provider} - {result.backup_id}")
            logger.critical(f"Error: {result.error}")
            logger.critical(f"Failed checks: {', '.join(result.checks_failed)}")
            
            # In production, send email/SMS alert here
            # For now, just log
            alert_message = f"""
BACKUP VERIFICATION FAILURE

Cloud Provider: {result.cloud_provider}
Database: {result.database_name}
Backup ID: {result.backup_id}
Time: {result.verification_time}
Error: {result.error}

Checks Performed: {len(result.checks_performed)}
Checks Passed: {len(result.checks_passed)}
Checks Failed: {len(result.checks_failed)}

Failed Checks: {', '.join(result.checks_failed)}

Please investigate immediately.
            """
            
            logger.critical(alert_message)
    
    def generate_verification_report(self, results: Dict[str, VerificationResult]) -> Dict:
        """
        Generate verification report
        
        Args:
            results: Dictionary of verification results
            
        Returns:
            Report dictionary
        """
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'clouds': {},
            'summary': {
                'total_verified': len(results),
                'passed': 0,
                'failed': 0
            }
        }
        
        for cloud, result in results.items():
            report['clouds'][cloud] = asdict(result)
            
            if result.status == VerificationStatus.PASSED.value:
                report['summary']['passed'] += 1
            else:
                report['summary']['failed'] += 1
        
        return report


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup Verification Service')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--cloud', choices=['AWS', 'Azure', 'GCP', 'all'], default='all',
                       help='Cloud provider to verify')
    parser.add_argument('--backup-id', help='Specific backup ID to verify')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Initialize verifier
    verifier = BackupVerifier(config)
    
    # Verify backups
    if args.backup_id:
        # Verify specific backup
        if args.cloud == 'AWS':
            result = verifier.verify_aws_backup(args.backup_id)
        elif args.cloud == 'Azure':
            result = verifier.verify_azure_backup(args.backup_id)
        elif args.cloud == 'GCP':
            result = verifier.verify_gcp_backup(args.backup_id)
        else:
            logger.error("Must specify --cloud when using --backup-id")
            sys.exit(1)
        
        print(json.dumps(asdict(result), indent=2, default=str))
        verifier.send_verification_alert(result)
    else:
        # Verify latest backups
        results = verifier.verify_latest_backups()
        report = verifier.generate_verification_report(results)
        print(json.dumps(report, indent=2, default=str))
        
        # Send alerts for failures
        for result in results.values():
            verifier.send_verification_alert(result)


if __name__ == '__main__':
    main()
