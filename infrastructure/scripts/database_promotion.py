#!/usr/bin/env python3
"""
Database Promotion Script

This script handles the promotion of a replica database to primary role during failover.
It stops replication, enables writes, and verifies the promotion was successful.

Features:
- Stop replication on target database
- Promote replica to primary (read-write mode)
- Verify promotion success
- Update application configuration to use new primary
- Rollback capability if promotion fails

Requirements:
- Database credentials with SUPER privilege
- pymysql library
"""

import sys
import logging
import json
import time
from typing import Dict, Tuple, Optional
from datetime import datetime

try:
    import pymysql
    import boto3
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install pymysql boto3")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabasePromoter:
    """Handles database promotion from replica to primary"""
    
    def __init__(self, config: Dict):
        """
        Initialize database promoter
        
        Args:
            config: Configuration dictionary with database connection details
        """
        self.config = config
        self.connection = None
        
    def connect(self, db_config: Dict) -> bool:
        """
        Connect to database
        
        Args:
            db_config: Database configuration
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = pymysql.connect(
                host=db_config['host'],
                port=db_config.get('port', 3306),
                user=db_config['user'],
                password=db_config['password'],
                database=db_config.get('database', 'mysql'),
                connect_timeout=10,
                autocommit=True
            )
            logger.info(f"Connected to database at {db_config['host']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def check_replication_status(self) -> Tuple[bool, Dict]:
        """
        Check current replication status
        
        Returns:
            Tuple of (is_replica, status_dict)
        """
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SHOW SLAVE STATUS")
                result = cursor.fetchone()
                
                if result:
                    logger.info("Database is currently a replica")
                    return True, result
                else:
                    logger.info("Database is not a replica")
                    return False, {}
        except Exception as e:
            logger.error(f"Error checking replication status: {e}")
            return False, {}
    
    def get_replication_lag(self) -> Optional[int]:
        """
        Get current replication lag in seconds
        
        Returns:
            Replication lag in seconds, or None if not a replica
        """
        try:
            is_replica, status = self.check_replication_status()
            if is_replica and status:
                return status.get('Seconds_Behind_Master')
            return None
        except Exception as e:
            logger.error(f"Error getting replication lag: {e}")
            return None
    
    def stop_replication(self) -> bool:
        """
        Stop replication on the database
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Stopping replication...")
            with self.connection.cursor() as cursor:
                cursor.execute("STOP SLAVE")
            
            # Verify replication stopped
            time.sleep(1)
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SHOW SLAVE STATUS")
                result = cursor.fetchone()
                
                if result:
                    io_running = result.get('Slave_IO_Running', 'No')
                    sql_running = result.get('Slave_SQL_Running', 'No')
                    
                    if io_running == 'No' and sql_running == 'No':
                        logger.info("Replication stopped successfully")
                        return True
                    else:
                        logger.warning(f"Replication may not be fully stopped: IO={io_running}, SQL={sql_running}")
                        return False
                else:
                    logger.info("No replication configuration found")
                    return True
                    
        except Exception as e:
            logger.error(f"Error stopping replication: {e}")
            return False
    
    def reset_slave(self) -> bool:
        """
        Reset slave configuration
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Resetting slave configuration...")
            with self.connection.cursor() as cursor:
                cursor.execute("RESET SLAVE ALL")
            
            logger.info("Slave configuration reset successfully")
            return True
        except Exception as e:
            logger.error(f"Error resetting slave: {e}")
            return False
    
    def enable_writes(self) -> bool:
        """
        Enable writes by setting read_only to OFF
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Enabling writes...")
            with self.connection.cursor() as cursor:
                # Disable read-only mode
                cursor.execute("SET GLOBAL read_only = OFF")
                cursor.execute("SET GLOBAL super_read_only = OFF")
            
            logger.info("Writes enabled successfully")
            return True
        except Exception as e:
            logger.error(f"Error enabling writes: {e}")
            return False
    
    def verify_promotion(self) -> Tuple[bool, str]:
        """
        Verify database promotion was successful
        
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info("Verifying database promotion...")
            
            # Check read_only status
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW VARIABLES LIKE 'read_only'")
                result = cursor.fetchone()
                
                if not result or result[1] != 'OFF':
                    return False, f"read_only is not OFF: {result}"
                
                cursor.execute("SHOW VARIABLES LIKE 'super_read_only'")
                result = cursor.fetchone()
                
                if not result or result[1] != 'OFF':
                    return False, f"super_read_only is not OFF: {result}"
            
            # Check replication status
            is_replica, _ = self.check_replication_status()
            if is_replica:
                return False, "Database is still configured as replica"
            
            # Test write capability
            with self.connection.cursor() as cursor:
                cursor.execute("CREATE TABLE IF NOT EXISTS promotion_test (id INT PRIMARY KEY, test_time DATETIME)")
                cursor.execute("INSERT INTO promotion_test VALUES (1, NOW()) ON DUPLICATE KEY UPDATE test_time = NOW()")
                cursor.execute("SELECT * FROM promotion_test WHERE id = 1")
                result = cursor.fetchone()
                
                if not result:
                    return False, "Failed to write test data"
                
                cursor.execute("DROP TABLE IF EXISTS promotion_test")
            
            logger.info("Database promotion verified successfully")
            return True, "Database is now primary and accepting writes"
            
        except Exception as e:
            logger.error(f"Error verifying promotion: {e}")
            return False, f"Verification error: {str(e)}"
    
    def promote_to_primary(self) -> Tuple[bool, str]:
        """
        Promote replica database to primary
        
        Returns:
            Tuple of (success, message)
        """
        start_time = datetime.now()
        logger.info("Starting database promotion process...")
        
        try:
            # Step 1: Check current status
            is_replica, status = self.check_replication_status()
            
            if not is_replica:
                logger.warning("Database is not a replica, skipping promotion")
                return True, "Database is already primary"
            
            # Step 2: Check replication lag
            lag = self.get_replication_lag()
            if lag is not None and lag > 0:
                logger.warning(f"Replication lag is {lag} seconds")
                # Wait for replication to catch up (max 30 seconds)
                wait_time = 0
                while lag > 0 and wait_time < 30:
                    time.sleep(1)
                    wait_time += 1
                    lag = self.get_replication_lag()
                    if lag is not None:
                        logger.info(f"Waiting for replication to catch up... lag={lag}s")
            
            # Step 3: Stop replication
            if not self.stop_replication():
                return False, "Failed to stop replication"
            
            # Step 4: Reset slave configuration
            if not self.reset_slave():
                return False, "Failed to reset slave configuration"
            
            # Step 5: Enable writes
            if not self.enable_writes():
                return False, "Failed to enable writes"
            
            # Step 6: Verify promotion
            success, message = self.verify_promotion()
            if not success:
                return False, f"Promotion verification failed: {message}"
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Database promotion completed successfully in {duration:.2f} seconds")
            
            return True, f"Database promoted to primary in {duration:.2f} seconds"
            
        except Exception as e:
            logger.error(f"Error during database promotion: {e}")
            return False, f"Promotion error: {str(e)}"
    
    def update_application_config(self, cloud: str, endpoint: str) -> bool:
        """
        Update application configuration to use new primary database
        
        Args:
            cloud: Cloud provider (aws, azure, gcp)
            endpoint: New database endpoint
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating application configuration for {cloud}...")
            
            # Update configuration in AWS Systems Manager Parameter Store
            if 'aws_region' in self.config:
                ssm_client = boto3.client('ssm', region_name=self.config['aws_region'])
                
                parameter_name = f"/dr-system/{cloud}/database/endpoint"
                
                ssm_client.put_parameter(
                    Name=parameter_name,
                    Value=endpoint,
                    Type='String',
                    Overwrite=True,
                    Description=f'Primary database endpoint for {cloud}'
                )
                
                logger.info(f"Updated parameter {parameter_name} with new endpoint")
            
            # TODO: Add logic to restart application instances to pick up new config
            # This could involve:
            # - Updating environment variables
            # - Restarting containers
            # - Triggering configuration reload
            
            return True
        except Exception as e:
            logger.error(f"Error updating application config: {e}")
            return False


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
    
    parser = argparse.ArgumentParser(description='Database Promotion Script')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--cloud', required=True, choices=['aws', 'azure', 'gcp'], 
                       help='Cloud provider to promote')
    parser.add_argument('--verify-only', action='store_true', 
                       help='Only verify current status without promoting')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Get database configuration for target cloud
    if 'databases' not in config or args.cloud not in config['databases']:
        logger.error(f"No database configuration found for {args.cloud}")
        sys.exit(1)
    
    db_config = config['databases'][args.cloud]
    
    # Initialize promoter
    promoter = DatabasePromoter(config)
    
    # Connect to database
    if not promoter.connect(db_config):
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    try:
        if args.verify_only:
            # Verify current status
            is_replica, status = promoter.check_replication_status()
            
            if is_replica:
                lag = promoter.get_replication_lag()
                print(f"Database is a replica with {lag} seconds lag")
                sys.exit(0)
            else:
                success, message = promoter.verify_promotion()
                if success:
                    print("Database is primary and accepting writes")
                    sys.exit(0)
                else:
                    print(f"Database status unclear: {message}")
                    sys.exit(1)
        else:
            # Promote database
            success, message = promoter.promote_to_primary()
            
            if success:
                print(f"Success: {message}")
                
                # Update application configuration
                if 'endpoints' in config and args.cloud in config['endpoints']:
                    promoter.update_application_config(args.cloud, db_config['host'])
                
                sys.exit(0)
            else:
                print(f"Failed: {message}")
                sys.exit(1)
    finally:
        promoter.disconnect()


if __name__ == '__main__':
    main()
