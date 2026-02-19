#!/usr/bin/env python3
"""
Failback Script

This script handles the failback process to return to the original primary cloud
after a failover event. It verifies the source cloud is healthy, reverses replication
direction, and updates DNS to point back to the original primary.

Features:
- Verify source cloud health before failback
- Reverse replication direction
- Promote original primary back to primary role
- Update DNS to point back to original primary
- Comprehensive logging and notifications

Requirements:
- Source cloud must be healthy
- Current active cloud must be stable
- Database replication must be functional
"""

import sys
import logging
import json
import time
from typing import Dict, Tuple
from datetime import datetime

try:
    import boto3
    import pymysql
    import requests
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install boto3 pymysql requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FailbackOrchestrator:
    """Orchestrates failback to original primary cloud"""
    
    def __init__(self, config: Dict):
        """
        Initialize failback orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize AWS clients
        aws_region = config.get('aws_region', 'us-east-1')
        self.route53_client = boto3.client('route53', region_name=aws_region)
        self.sns_client = boto3.client('sns', region_name=aws_region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=aws_region)
        
        logger.info("Failback Orchestrator initialized")
    
    def verify_source_health(self, source_cloud: str) -> Tuple[bool, str]:
        """
        Verify source cloud is healthy before failback
        
        Args:
            source_cloud: Source cloud to failback to (aws, azure, gcp)
            
        Returns:
            Tuple of (is_healthy, message)
        """
        logger.info(f"Verifying {source_cloud} health...")
        
        try:
            # Check health check status
            if 'health_checks' in self.config and source_cloud in self.config['health_checks']:
                health_check_id = self.config['health_checks'][source_cloud]
                
                response = self.route53_client.get_health_check_status(
                    HealthCheckId=health_check_id
                )
                
                if response['HealthCheckObservations']:
                    healthy_count = sum(
                        1 for obs in response['HealthCheckObservations']
                        if obs['StatusReport']['Status'] == 'Success'
                    )
                    total_count = len(response['HealthCheckObservations'])
                    
                    if healthy_count / total_count < 0.8:
                        return False, f"Health check failed ({healthy_count}/{total_count} checkers healthy)"
            
            # Check database connectivity
            if 'databases' in self.config and source_cloud in self.config['databases']:
                db_config = self.config['databases'][source_cloud]
                
                try:
                    connection = pymysql.connect(
                        host=db_config['host'],
                        user=db_config['user'],
                        password=db_config['password'],
                        database=db_config.get('database', 'mysql'),
                        connect_timeout=5
                    )
                    connection.close()
                except Exception as e:
                    return False, f"Database connection failed: {str(e)}"
            
            # Check application endpoint
            if 'endpoints' in self.config and source_cloud in self.config['endpoints']:
                endpoint = self.config['endpoints'][source_cloud]
                
                try:
                    response = requests.get(f"{endpoint}/health", timeout=10)
                    if response.status_code != 200:
                        return False, f"Application returned status {response.status_code}"
                except Exception as e:
                    return False, f"Application health check failed: {str(e)}"
            
            logger.info(f"{source_cloud} is healthy and ready for failback")
            return True, "Source cloud is healthy"
            
        except Exception as e:
            logger.error(f"Error verifying source health: {e}")
            return False, f"Error: {str(e)}"
    
    def setup_reverse_replication(self, current_primary: str, new_primary: str) -> Tuple[bool, str]:
        """
        Setup replication from current primary to new primary
        
        Args:
            current_primary: Current active cloud
            new_primary: Cloud to failback to
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Setting up reverse replication from {current_primary} to {new_primary}...")
        
        try:
            # Get database configurations
            if 'databases' not in self.config:
                return False, "No database configuration found"
            
            current_db = self.config['databases'].get(current_primary)
            new_db = self.config['databases'].get(new_primary)
            
            if not current_db or not new_db:
                return False, "Database configuration missing for one or both clouds"
            
            # Connect to new primary (will become primary after failback)
            connection = pymysql.connect(
                host=new_db['host'],
                user=new_db['user'],
                password=new_db['password'],
                database=new_db.get('database', 'mysql'),
                connect_timeout=10,
                autocommit=True
            )
            
            with connection.cursor() as cursor:
                # Configure replication from current primary
                logger.info("Configuring replication...")
                
                # Note: This is a simplified example. In production, you would need:
                # 1. Get binary log position from current primary
                # 2. Take a consistent snapshot if needed
                # 3. Configure CHANGE MASTER TO with correct coordinates
                
                change_master_sql = f"""
                CHANGE MASTER TO
                    MASTER_HOST='{current_db['host']}',
                    MASTER_USER='{current_db.get('replication_user', current_db['user'])}',
                    MASTER_PASSWORD='{current_db.get('replication_password', current_db['password'])}',
                    MASTER_PORT={current_db.get('port', 3306)},
                    MASTER_AUTO_POSITION=1
                """
                
                cursor.execute(change_master_sql)
                cursor.execute("START SLAVE")
                
                # Wait a moment for replication to start
                time.sleep(2)
                
                # Check replication status
                cursor.execute("SHOW SLAVE STATUS")
                result = cursor.fetchone()
                
                if result:
                    logger.info("Reverse replication configured successfully")
                    connection.close()
                    return True, "Reverse replication setup complete"
                else:
                    connection.close()
                    return False, "Failed to verify replication setup"
            
        except Exception as e:
            logger.error(f"Error setting up reverse replication: {e}")
            return False, f"Error: {str(e)}"
    
    def promote_original_primary(self, source_cloud: str) -> Tuple[bool, str]:
        """
        Promote original primary back to primary role
        
        Args:
            source_cloud: Cloud to promote
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Promoting {source_cloud} back to primary...")
        
        try:
            db_config = self.config['databases'][source_cloud]
            
            connection = pymysql.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config.get('database', 'mysql'),
                connect_timeout=10,
                autocommit=True
            )
            
            with connection.cursor() as cursor:
                # Stop replication
                cursor.execute("STOP SLAVE")
                
                # Reset slave configuration
                cursor.execute("RESET SLAVE ALL")
                
                # Enable writes
                cursor.execute("SET GLOBAL read_only = OFF")
                cursor.execute("SET GLOBAL super_read_only = OFF")
                
                # Verify
                cursor.execute("SHOW VARIABLES LIKE 'read_only'")
                result = cursor.fetchone()
                
                if result and result[1] == 'OFF':
                    logger.info(f"{source_cloud} promoted to primary successfully")
                    connection.close()
                    return True, "Original primary promoted successfully"
                else:
                    connection.close()
                    return False, "Failed to verify promotion"
            
        except Exception as e:
            logger.error(f"Error promoting original primary: {e}")
            return False, f"Error: {str(e)}"
    
    def demote_current_primary(self, current_cloud: str, new_primary_cloud: str) -> Tuple[bool, str]:
        """
        Demote current primary to replica
        
        Args:
            current_cloud: Current active cloud to demote
            new_primary_cloud: New primary cloud
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Demoting {current_cloud} to replica...")
        
        try:
            current_db = self.config['databases'][current_cloud]
            new_primary_db = self.config['databases'][new_primary_cloud]
            
            connection = pymysql.connect(
                host=current_db['host'],
                user=current_db['user'],
                password=current_db['password'],
                database=current_db.get('database', 'mysql'),
                connect_timeout=10,
                autocommit=True
            )
            
            with connection.cursor() as cursor:
                # Enable read-only mode
                cursor.execute("SET GLOBAL read_only = ON")
                cursor.execute("SET GLOBAL super_read_only = ON")
                
                # Configure as replica of new primary
                change_master_sql = f"""
                CHANGE MASTER TO
                    MASTER_HOST='{new_primary_db['host']}',
                    MASTER_USER='{new_primary_db.get('replication_user', new_primary_db['user'])}',
                    MASTER_PASSWORD='{new_primary_db.get('replication_password', new_primary_db['password'])}',
                    MASTER_PORT={new_primary_db.get('port', 3306)},
                    MASTER_AUTO_POSITION=1
                """
                
                cursor.execute(change_master_sql)
                cursor.execute("START SLAVE")
                
                logger.info(f"{current_cloud} demoted to replica successfully")
                connection.close()
                return True, "Current primary demoted to replica"
            
        except Exception as e:
            logger.error(f"Error demoting current primary: {e}")
            return False, f"Error: {str(e)}"
    
    def update_dns(self, target_cloud: str) -> Tuple[bool, str]:
        """
        Update DNS to point back to original primary
        
        Args:
            target_cloud: Target cloud for DNS
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Updating DNS to point to {target_cloud}...")
        
        try:
            import subprocess
            import os
            
            # Call DNS failover script
            dns_script = os.path.join(
                os.path.dirname(__file__),
                'dns_failover.py'
            )
            
            result = subprocess.run(
                [sys.executable, dns_script, '--target', target_cloud],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"DNS updated successfully to {target_cloud}")
                return True, "DNS updated successfully"
            else:
                logger.error(f"DNS update failed: {result.stderr}")
                return False, f"DNS update failed: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error updating DNS: {e}")
            return False, f"Error: {str(e)}"
    
    def send_notification(self, message: str, subject: str):
        """Send notification via SNS"""
        try:
            if 'sns_topic_arn' in self.config:
                self.sns_client.publish(
                    TopicArn=self.config['sns_topic_arn'],
                    Subject=subject,
                    Message=message
                )
                logger.info("Notification sent successfully")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def execute_failback(self, source_cloud: str, current_cloud: str) -> Tuple[bool, str]:
        """
        Execute complete failback process
        
        Args:
            source_cloud: Original primary cloud to failback to
            current_cloud: Current active cloud
            
        Returns:
            Tuple of (success, message)
        """
        start_time = datetime.now()
        logger.info(f"Starting failback from {current_cloud} to {source_cloud}")
        
        steps = []
        
        try:
            # Step 1: Verify source cloud health
            logger.info("Step 1: Verifying source cloud health...")
            is_healthy, health_msg = self.verify_source_health(source_cloud)
            steps.append(f"✓ Verify source health: {health_msg}" if is_healthy else f"✗ Verify source health: {health_msg}")
            
            if not is_healthy:
                self.send_notification(
                    f"Failback failed: Source cloud {source_cloud} is not healthy\n{health_msg}",
                    f"Failback Failed: {current_cloud} → {source_cloud}"
                )
                return False, f"Source cloud not healthy: {health_msg}"
            
            # Step 2: Setup reverse replication (optional, for data sync)
            logger.info("Step 2: Setting up reverse replication...")
            success, repl_msg = self.setup_reverse_replication(current_cloud, source_cloud)
            steps.append(f"✓ Setup reverse replication: {repl_msg}" if success else f"⚠ Setup reverse replication: {repl_msg}")
            
            # Wait for replication to catch up
            if success:
                logger.info("Waiting for replication to catch up...")
                time.sleep(10)
            
            # Step 3: Promote original primary
            logger.info("Step 3: Promoting original primary...")
            success, promote_msg = self.promote_original_primary(source_cloud)
            steps.append(f"✓ Promote original primary: {promote_msg}" if success else f"✗ Promote original primary: {promote_msg}")
            
            if not success:
                self.send_notification(
                    f"Failback failed: Could not promote {source_cloud}\n{promote_msg}",
                    f"Failback Failed: {current_cloud} → {source_cloud}"
                )
                return False, f"Failed to promote original primary: {promote_msg}"
            
            # Step 4: Update DNS
            logger.info("Step 4: Updating DNS...")
            success, dns_msg = self.update_dns(source_cloud)
            steps.append(f"✓ Update DNS: {dns_msg}" if success else f"✗ Update DNS: {dns_msg}")
            
            if not success:
                self.send_notification(
                    f"Failback partially failed: DNS update failed\n{dns_msg}",
                    f"Failback Warning: {current_cloud} → {source_cloud}"
                )
                return False, f"Failed to update DNS: {dns_msg}"
            
            # Step 5: Demote current primary to replica
            logger.info("Step 5: Demoting current primary to replica...")
            success, demote_msg = self.demote_current_primary(current_cloud, source_cloud)
            steps.append(f"✓ Demote current primary: {demote_msg}" if success else f"⚠ Demote current primary: {demote_msg}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Send success notification
            message = f"""
Failback completed successfully!

Source Cloud: {current_cloud}
Target Cloud: {source_cloud}
Duration: {duration:.2f} seconds
Timestamp: {datetime.now()}

Steps Completed:
"""
            for step in steps:
                message += f"{step}\n"
            
            self.send_notification(message, f"Failback Successful: {current_cloud} → {source_cloud}")
            
            logger.info(f"Failback completed successfully in {duration:.2f} seconds")
            return True, f"Failback completed in {duration:.2f} seconds"
            
        except Exception as e:
            logger.error(f"Error during failback: {e}")
            self.send_notification(
                f"Failback failed with error: {str(e)}",
                f"Failback Error: {current_cloud} → {source_cloud}"
            )
            return False, f"Failback error: {str(e)}"


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
    
    parser = argparse.ArgumentParser(description='Failback Script')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--source', required=True, choices=['aws', 'azure', 'gcp'],
                       help='Original primary cloud to failback to')
    parser.add_argument('--current', required=True, choices=['aws', 'azure', 'gcp'],
                       help='Current active cloud')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify source cloud health without executing failback')
    
    args = parser.parse_args()
    
    if args.source == args.current:
        logger.error("Source and current cloud cannot be the same")
        sys.exit(1)
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize orchestrator
    orchestrator = FailbackOrchestrator(config)
    
    if args.verify_only:
        # Verify source cloud health only
        is_healthy, message = orchestrator.verify_source_health(args.source)
        
        if is_healthy:
            print(f"Source cloud {args.source} is healthy and ready for failback")
            print(f"Details: {message}")
            sys.exit(0)
        else:
            print(f"Source cloud {args.source} is not ready for failback")
            print(f"Reason: {message}")
            sys.exit(1)
    else:
        # Execute failback
        success, message = orchestrator.execute_failback(args.source, args.current)
        
        if success:
            print(f"Failback successful: {message}")
            sys.exit(0)
        else:
            print(f"Failback failed: {message}")
            sys.exit(1)


if __name__ == '__main__':
    main()
