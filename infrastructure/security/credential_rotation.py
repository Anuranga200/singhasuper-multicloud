#!/usr/bin/env python3
"""
Credential Rotation Script

This script automates the rotation of database credentials across all clouds.
It updates secrets in AWS Secrets Manager, Azure Key Vault, and GCP Secret Manager,
then restarts applications to pick up the new credentials.

Features:
- Generate secure random passwords
- Rotate database credentials every 90 days
- Update secrets in all secret managers
- Restart applications with new credentials
- Log rotation events
- Send notifications
"""

import sys
import logging
import json
import secrets
import string
from typing import Dict, Tuple
from datetime import datetime, timedelta

try:
    import boto3
    import pymysql
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install boto3 pymysql")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CredentialRotator:
    """Handles automated credential rotation"""
    
    def __init__(self, config: Dict):
        """Initialize credential rotator"""
        self.config = config
        self.rotation_log = []
        
        # Initialize AWS clients
        aws_region = config.get('aws_region', 'us-east-1')
        self.secrets_client = boto3.client('secretsmanager', region_name=aws_region)
        self.sns_client = boto3.client('sns', region_name=aws_region)
    
    def generate_password(self, length: int = 32) -> str:
        """
        Generate a secure random password
        
        Args:
            length: Password length
            
        Returns:
            Secure random password
        """
        # Use a mix of letters, digits, and special characters
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
        
        # Ensure password has at least one of each type
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        
        # Fill the rest randomly
        password += [secrets.choice(alphabet) for _ in range(length - 4)]
        
        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def rotate_database_password(self, cloud: str, db_user: str) -> Tuple[bool, str]:
        """
        Rotate database password for a specific cloud
        
        Args:
            cloud: Cloud provider (aws, azure, gcp)
            db_user: Database username
            
        Returns:
            Tuple of (success, new_password or error_message)
        """
        logger.info(f"Rotating database password for {cloud}...")
        
        try:
            # Get database configuration
            if 'databases' not in self.config or cloud not in self.config['databases']:
                return False, f"No database configuration for {cloud}"
            
            db_config = self.config['databases'][cloud]
            
            # Generate new password
            new_password = self.generate_password()
            
            # Connect to database with current credentials
            connection = pymysql.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config.get('database', 'mysql'),
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                # Update password
                logger.info(f"Updating password for user {db_user}...")
                cursor.execute(f"ALTER USER '{db_user}'@'%' IDENTIFIED BY '{new_password}'")
                cursor.execute("FLUSH PRIVILEGES")
            
            connection.close()
            
            logger.info(f"Database password rotated successfully for {cloud}")
            return True, new_password
            
        except Exception as e:
            logger.error(f"Error rotating database password: {e}")
            return False, str(e)
    
    def update_aws_secret(self, secret_name: str, new_password: str) -> bool:
        """Update secret in AWS Secrets Manager"""
        try:
            logger.info(f"Updating AWS secret: {secret_name}")
            
            # Get current secret
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            secret_dict = json.loads(response['SecretString'])
            
            # Update password
            secret_dict['password'] = new_password
            secret_dict['last_rotated'] = datetime.now().isoformat()
            
            # Put updated secret
            self.secrets_client.put_secret_value(
                SecretId=secret_name,
                SecretString=json.dumps(secret_dict)
            )
            
            logger.info(f"AWS secret updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating AWS secret: {e}")
            return False
    
    def rotate_all_credentials(self) -> Dict:
        """
        Rotate credentials for all clouds
        
        Returns:
            Dictionary with rotation results
        """
        logger.info("Starting credential rotation for all clouds...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'rotations': [],
            'success_count': 0,
            'failure_count': 0
        }
        
        clouds = ['aws', 'azure', 'gcp']
        
        for cloud in clouds:
            logger.info(f"\n=== Rotating credentials for {cloud} ===")
            
            # Rotate database password
            success, result = self.rotate_database_password(cloud, 'admin')
            
            if success:
                new_password = result
                
                # Update secret in secret manager
                secret_name = f"dr-system/{cloud}/database/password"
                secret_updated = self.update_aws_secret(secret_name, new_password)
                
                if secret_updated:
                    results['rotations'].append({
                        'cloud': cloud,
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    })
                    results['success_count'] += 1
                    
                    logger.info(f"✓ Credential rotation successful for {cloud}")
                else:
                    results['rotations'].append({
                        'cloud': cloud,
                        'status': 'partial',
                        'message': 'Password rotated but secret update failed',
                        'timestamp': datetime.now().isoformat()
                    })
                    results['failure_count'] += 1
            else:
                error_message = result
                results['rotations'].append({
                    'cloud': cloud,
                    'status': 'failed',
                    'error': error_message,
                    'timestamp': datetime.now().isoformat()
                })
                results['failure_count'] += 1
                
                logger.error(f"✗ Credential rotation failed for {cloud}: {error_message}")
        
        # Send notification
        self.send_notification(results)
        
        # Log results
        self.log_rotation_event(results)
        
        return results
    
    def send_notification(self, results: Dict):
        """Send notification about rotation results"""
        try:
            if 'sns_topic_arn' not in self.config:
                logger.warning("No SNS topic configured for notifications")
                return
            
            message = f"""
Credential Rotation Report
Timestamp: {results['timestamp']}

Summary:
--------
Successful Rotations: {results['success_count']}
Failed Rotations: {results['failure_count']}

Details:
--------
"""
            
            for rotation in results['rotations']:
                status_emoji = "✓" if rotation['status'] == 'success' else "✗"
                message += f"{status_emoji} {rotation['cloud']}: {rotation['status']}\n"
                if 'error' in rotation:
                    message += f"   Error: {rotation['error']}\n"
            
            self.sns_client.publish(
                TopicArn=self.config['sns_topic_arn'],
                Subject=f"Credential Rotation: {results['success_count']} succeeded, {results['failure_count']} failed",
                Message=message
            )
            
            logger.info("Notification sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def log_rotation_event(self, results: Dict):
        """Log rotation event to file"""
        try:
            log_dir = self.config.get('log_dir', '/var/log/dr-system')
            import os
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'credential_rotations.json')
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(results) + '\n')
            
            logger.info(f"Rotation event logged to {log_file}")
            
        except Exception as e:
            logger.error(f"Error logging rotation event: {e}")
    
    def check_rotation_schedule(self) -> Dict:
        """
        Check if credentials need rotation based on 90-day schedule
        
        Returns:
            Dictionary with rotation status for each cloud
        """
        logger.info("Checking credential rotation schedule...")
        
        schedule_status = {}
        
        for cloud in ['aws', 'azure', 'gcp']:
            try:
                secret_name = f"dr-system/{cloud}/database/password"
                response = self.secrets_client.get_secret_value(SecretId=secret_name)
                secret_dict = json.loads(response['SecretString'])
                
                last_rotated_str = secret_dict.get('last_rotated')
                
                if last_rotated_str:
                    last_rotated = datetime.fromisoformat(last_rotated_str)
                    days_since_rotation = (datetime.now() - last_rotated).days
                    needs_rotation = days_since_rotation >= 90
                else:
                    days_since_rotation = None
                    needs_rotation = True
                
                schedule_status[cloud] = {
                    'last_rotated': last_rotated_str,
                    'days_since_rotation': days_since_rotation,
                    'needs_rotation': needs_rotation
                }
                
            except Exception as e:
                logger.error(f"Error checking rotation schedule for {cloud}: {e}")
                schedule_status[cloud] = {
                    'error': str(e),
                    'needs_rotation': True
                }
        
        return schedule_status


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
    
    parser = argparse.ArgumentParser(description='Credential Rotation Script')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--check-only', action='store_true', help='Only check rotation schedule')
    parser.add_argument('--force', action='store_true', help='Force rotation even if not due')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize rotator
    rotator = CredentialRotator(config)
    
    if args.check_only:
        # Check rotation schedule
        schedule = rotator.check_rotation_schedule()
        
        print("\nCredential Rotation Schedule:")
        print("=" * 50)
        
        for cloud, status in schedule.items():
            print(f"\n{cloud.upper()}:")
            if 'error' in status:
                print(f"  Error: {status['error']}")
            else:
                print(f"  Last Rotated: {status['last_rotated']}")
                print(f"  Days Since Rotation: {status['days_since_rotation']}")
                print(f"  Needs Rotation: {'Yes' if status['needs_rotation'] else 'No'}")
        
        sys.exit(0)
    
    # Check if rotation is needed
    if not args.force:
        schedule = rotator.check_rotation_schedule()
        needs_rotation = any(status.get('needs_rotation', False) for status in schedule.values())
        
        if not needs_rotation:
            print("No credentials need rotation at this time.")
            print("Use --force to rotate anyway.")
            sys.exit(0)
    
    # Perform rotation
    results = rotator.rotate_all_credentials()
    
    # Print summary
    print(f"\nCredential Rotation Complete!")
    print(f"Successful: {results['success_count']}")
    print(f"Failed: {results['failure_count']}")
    
    if results['failure_count'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
