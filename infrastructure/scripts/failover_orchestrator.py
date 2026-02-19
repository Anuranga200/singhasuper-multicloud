#!/usr/bin/env python3
"""
Failover Orchestration Service

This script orchestrates automated failover between clouds when failures are detected.
It integrates with the health monitoring system and DNS failover to provide end-to-end
automated disaster recovery.

Features:
- Detects failures from health monitor
- Verifies target cloud health before failover
- Promotes replica database to primary
- Updates DNS records
- Sends notifications
- Logs failover events with timestamps

Requirements:
- Health monitoring system running
- Database replication configured
- DNS failover script available
- AWS credentials with necessary permissions
"""

import sys
import time
import logging
import json
import os
import subprocess
from typing import Dict, Optional, Tuple, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

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


class CloudProvider(Enum):
    """Cloud provider enumeration"""
    AWS = "AWS"
    AZURE = "Azure"
    GCP = "GCP"


class FailoverStatus(Enum):
    """Failover status enumeration"""
    INITIATED = "initiated"
    VERIFYING_TARGET = "verifying_target"
    PROMOTING_DATABASE = "promoting_database"
    UPDATING_DNS = "updating_dns"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class FailoverStep:
    """Individual failover step"""
    name: str
    status: str  # pending, in_progress, completed, failed
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class FailoverEvent:
    """Failover event data"""
    event_id: str
    timestamp: datetime
    source_cloud: str
    target_cloud: str
    reason: str
    status: str
    duration: Optional[float] = None
    rto: Optional[float] = None
    steps: List[FailoverStep] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []


class FailoverOrchestrator:
    """Orchestrates automated failover between clouds"""
    
    def __init__(self, config: Dict):
        """
        Initialize failover orchestrator
        
        Args:
            config: Configuration dictionary with cloud endpoints, credentials, etc.
        """
        self.config = config
        self.current_active_cloud = CloudProvider.AWS
        self.failover_events = []
        
        # Initialize AWS clients
        aws_region = config.get('aws_region', 'us-east-1')
        self.route53_client = boto3.client('route53', region_name=aws_region)
        self.sns_client = boto3.client('sns', region_name=aws_region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=aws_region)
        
        logger.info("Failover Orchestrator initialized")
    
    def detect_failure(self, cloud: CloudProvider) -> Tuple[bool, str]:
        """
        Detect if a cloud provider has failed
        
        Args:
            cloud: Cloud provider to check
            
        Returns:
            Tuple of (is_failed, reason)
        """
        try:
            cloud_key = cloud.value.lower()
            
            # Check if health check ID is configured
            if 'health_checks' not in self.config or cloud_key not in self.config['health_checks']:
                logger.warning(f"No health check configured for {cloud.value}")
                return False, "No health check configured"
            
            health_check_id = self.config['health_checks'][cloud_key]
            
            # Get health check status from Route 53
            response = self.route53_client.get_health_check_status(
                HealthCheckId=health_check_id
            )
            
            if not response['HealthCheckObservations']:
                return True, "No health check observations available"
            
            # Check if majority of checkers report unhealthy
            healthy_count = sum(
                1 for obs in response['HealthCheckObservations']
                if obs['StatusReport']['Status'] == 'Success'
            )
            total_count = len(response['HealthCheckObservations'])
            
            if healthy_count / total_count < 0.5:
                return True, f"Health check failed ({healthy_count}/{total_count} checkers healthy)"
            
            return False, "Healthy"
            
        except Exception as e:
            logger.error(f"Error detecting failure for {cloud.value}: {e}")
            return True, f"Error checking health: {str(e)}"
    
    def verify_target_health(self, target_cloud: CloudProvider) -> Tuple[bool, str]:
        """
        Verify target cloud is healthy before failover
        
        Args:
            target_cloud: Target cloud provider
            
        Returns:
            Tuple of (is_healthy, message)
        """
        logger.info(f"Verifying {target_cloud.value} health...")
        
        try:
            # Check health check status
            is_failed, reason = self.detect_failure(target_cloud)
            
            if is_failed:
                return False, f"Target cloud unhealthy: {reason}"
            
            # Check database connectivity
            db_healthy, db_message = self._check_database_health(target_cloud)
            if not db_healthy:
                return False, f"Database unhealthy: {db_message}"
            
            # Check application endpoint
            app_healthy, app_message = self._check_application_health(target_cloud)
            if not app_healthy:
                return False, f"Application unhealthy: {app_message}"
            
            logger.info(f"{target_cloud.value} is healthy and ready for failover")
            return True, "Target cloud is healthy"
            
        except Exception as e:
            logger.error(f"Error verifying target health: {e}")
            return False, f"Error: {str(e)}"
    
    def _check_database_health(self, cloud: CloudProvider) -> Tuple[bool, str]:
        """Check database connectivity and health"""
        try:
            cloud_key = cloud.value.lower()
            if 'databases' not in self.config or cloud_key not in self.config['databases']:
                return True, "No database configured"
            
            db_config = self.config['databases'][cloud_key]
            
            # Try to connect to database
            connection = pymysql.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database'],
                connect_timeout=5
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            connection.close()
            
            return True, "Database is healthy"
            
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"
    
    def _check_application_health(self, cloud: CloudProvider) -> Tuple[bool, str]:
        """Check application endpoint health"""
        try:
            cloud_key = cloud.value.lower()
            if 'endpoints' not in self.config or cloud_key not in self.config['endpoints']:
                return True, "No endpoint configured"
            
            endpoint = self.config['endpoints'][cloud_key]
            
            # Make HTTP request to health endpoint
            response = requests.get(f"{endpoint}/health", timeout=10)
            
            if response.status_code == 200:
                return True, "Application is healthy"
            else:
                return False, f"Application returned status {response.status_code}"
                
        except Exception as e:
            return False, f"Application health check failed: {str(e)}"
    
    def promote_database(self, target_cloud: CloudProvider) -> Tuple[bool, str]:
        """
        Promote replica database to primary
        
        Args:
            target_cloud: Target cloud provider
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Promoting {target_cloud.value} database to primary...")
        
        try:
            cloud_key = target_cloud.value.lower()
            if 'databases' not in self.config or cloud_key not in self.config['databases']:
                return False, "No database configured"
            
            db_config = self.config['databases'][cloud_key]
            
            # Connect to database
            connection = pymysql.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database'],
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                # Stop replication
                logger.info("Stopping replication...")
                cursor.execute("STOP SLAVE")
                
                # Reset slave configuration
                logger.info("Resetting slave configuration...")
                cursor.execute("RESET SLAVE ALL")
                
                # Enable writes (set read_only to OFF)
                logger.info("Enabling writes...")
                cursor.execute("SET GLOBAL read_only = OFF")
                cursor.execute("SET GLOBAL super_read_only = OFF")
                
                # Verify promotion
                cursor.execute("SHOW VARIABLES LIKE 'read_only'")
                result = cursor.fetchone()
                
                if result and result[1] == 'OFF':
                    logger.info(f"{target_cloud.value} database promoted to primary successfully")
                    connection.close()
                    return True, "Database promoted successfully"
                else:
                    connection.close()
                    return False, "Failed to verify database promotion"
            
        except Exception as e:
            logger.error(f"Error promoting database: {e}")
            return False, f"Error: {str(e)}"
    
    def update_dns(self, target_cloud: CloudProvider) -> Tuple[bool, str]:
        """
        Update DNS records to point to target cloud
        
        Args:
            target_cloud: Target cloud provider
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Updating DNS to point to {target_cloud.value}...")
        
        try:
            # Call DNS failover script
            dns_script = os.path.join(
                os.path.dirname(__file__),
                'dns_failover.py'
            )
            
            cloud_key = target_cloud.value.lower()
            
            result = subprocess.run(
                [sys.executable, dns_script, '--target', cloud_key],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"DNS updated successfully to {target_cloud.value}")
                return True, "DNS updated successfully"
            else:
                logger.error(f"DNS update failed: {result.stderr}")
                return False, f"DNS update failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "DNS update timed out"
        except Exception as e:
            logger.error(f"Error updating DNS: {e}")
            return False, f"Error: {str(e)}"
    
    def send_notification(self, event: FailoverEvent):
        """
        Send notification about failover event
        
        Args:
            event: Failover event to notify about
        """
        try:
            if 'sns_topic_arn' not in self.config:
                logger.warning("No SNS topic configured for notifications")
                return
            
            message = f"""
Failover Event: {event.event_id}
Status: {event.status}
Source Cloud: {event.source_cloud}
Target Cloud: {event.target_cloud}
Reason: {event.reason}
Timestamp: {event.timestamp}
Duration: {event.duration:.2f} seconds
RTO: {event.rto:.2f} seconds

Steps Completed:
"""
            for step in event.steps:
                status_emoji = "✓" if step.status == "completed" else "✗"
                message += f"{status_emoji} {step.name}: {step.status}\n"
            
            self.sns_client.publish(
                TopicArn=self.config['sns_topic_arn'],
                Subject=f"Failover {event.status}: {event.source_cloud} → {event.target_cloud}",
                Message=message
            )
            
            logger.info("Notification sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def log_failover_event(self, event: FailoverEvent):
        """
        Log failover event to file and CloudWatch
        
        Args:
            event: Failover event to log
        """
        try:
            # Log to file
            log_dir = self.config.get('log_dir', '/var/log/dr-system')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'failover_events.json')
            
            # Convert event to dict
            event_dict = asdict(event)
            event_dict['timestamp'] = event.timestamp.isoformat()
            for step in event_dict['steps']:
                step['start_time'] = step['start_time'].isoformat()
                if step['end_time']:
                    step['end_time'] = step['end_time'].isoformat()
            
            # Append to log file
            with open(log_file, 'a') as f:
                f.write(json.dumps(event_dict) + '\n')
            
            # Log to CloudWatch
            self.cloudwatch_client.put_metric_data(
                Namespace='DR-System',
                MetricData=[
                    {
                        'MetricName': 'FailoverDuration',
                        'Value': event.duration or 0,
                        'Unit': 'Seconds',
                        'Timestamp': event.timestamp,
                        'Dimensions': [
                            {'Name': 'SourceCloud', 'Value': event.source_cloud},
                            {'Name': 'TargetCloud', 'Value': event.target_cloud}
                        ]
                    },
                    {
                        'MetricName': 'RTO',
                        'Value': event.rto or 0,
                        'Unit': 'Seconds',
                        'Timestamp': event.timestamp,
                        'Dimensions': [
                            {'Name': 'TargetCloud', 'Value': event.target_cloud}
                        ]
                    }
                ]
            )
            
            logger.info(f"Failover event logged: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Error logging failover event: {e}")
    
    def initiate_failover(self, target_cloud: CloudProvider, reason: str) -> FailoverEvent:
        """
        Initiate failover to target cloud
        
        Args:
            target_cloud: Target cloud provider
            reason: Reason for failover
            
        Returns:
            FailoverEvent with results
        """
        event_id = f"failover-{int(time.time())}"
        start_time = datetime.now()
        
        event = FailoverEvent(
            event_id=event_id,
            timestamp=start_time,
            source_cloud=self.current_active_cloud.value,
            target_cloud=target_cloud.value,
            reason=reason,
            status=FailoverStatus.INITIATED.value,
            steps=[]
        )
        
        logger.info(f"Initiating failover from {self.current_active_cloud.value} to {target_cloud.value}")
        logger.info(f"Reason: {reason}")
        
        try:
            # Step 1: Verify target cloud health
            step = FailoverStep(
                name="Verify target cloud health",
                status="in_progress",
                start_time=datetime.now()
            )
            event.steps.append(step)
            event.status = FailoverStatus.VERIFYING_TARGET.value
            
            is_healthy, health_message = self.verify_target_health(target_cloud)
            step.end_time = datetime.now()
            
            if not is_healthy:
                step.status = "failed"
                step.error = health_message
                event.status = FailoverStatus.FAILED.value
                event.duration = (datetime.now() - start_time).total_seconds()
                
                logger.error(f"Failover failed: {health_message}")
                self.log_failover_event(event)
                self.send_notification(event)
                return event
            
            step.status = "completed"
            logger.info("Target cloud health verified")
            
            # Step 2: Promote database
            step = FailoverStep(
                name="Promote replica database to primary",
                status="in_progress",
                start_time=datetime.now()
            )
            event.steps.append(step)
            event.status = FailoverStatus.PROMOTING_DATABASE.value
            
            success, db_message = self.promote_database(target_cloud)
            step.end_time = datetime.now()
            
            if not success:
                step.status = "failed"
                step.error = db_message
                event.status = FailoverStatus.FAILED.value
                event.duration = (datetime.now() - start_time).total_seconds()
                
                logger.error(f"Database promotion failed: {db_message}")
                self.log_failover_event(event)
                self.send_notification(event)
                return event
            
            step.status = "completed"
            logger.info("Database promoted successfully")
            
            # Step 3: Update DNS
            step = FailoverStep(
                name="Update DNS records",
                status="in_progress",
                start_time=datetime.now()
            )
            event.steps.append(step)
            event.status = FailoverStatus.UPDATING_DNS.value
            
            success, dns_message = self.update_dns(target_cloud)
            step.end_time = datetime.now()
            
            if not success:
                step.status = "failed"
                step.error = dns_message
                event.status = FailoverStatus.FAILED.value
                event.duration = (datetime.now() - start_time).total_seconds()
                
                logger.error(f"DNS update failed: {dns_message}")
                self.log_failover_event(event)
                self.send_notification(event)
                return event
            
            step.status = "completed"
            logger.info("DNS updated successfully")
            
            # Failover completed successfully
            event.status = FailoverStatus.COMPLETED.value
            event.duration = (datetime.now() - start_time).total_seconds()
            event.rto = event.duration
            
            self.current_active_cloud = target_cloud
            
            logger.info(f"Failover completed successfully in {event.duration:.2f} seconds")
            logger.info(f"Active cloud is now: {target_cloud.value}")
            
            # Log and notify
            self.log_failover_event(event)
            self.send_notification(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Unexpected error during failover: {e}")
            event.status = FailoverStatus.FAILED.value
            event.duration = (datetime.now() - start_time).total_seconds()
            
            # Add error step
            step = FailoverStep(
                name="Failover execution",
                status="failed",
                start_time=start_time,
                end_time=datetime.now(),
                error=str(e)
            )
            event.steps.append(step)
            
            self.log_failover_event(event)
            self.send_notification(event)
            
            return event
    
    def monitor_and_failover(self, check_interval: int = 30):
        """
        Continuously monitor clouds and initiate failover when needed
        
        Args:
            check_interval: Seconds between health checks
        """
        logger.info("Starting continuous monitoring...")
        logger.info(f"Check interval: {check_interval} seconds")
        
        consecutive_failures = {
            CloudProvider.AWS: 0,
            CloudProvider.AZURE: 0,
            CloudProvider.GCP: 0
        }
        
        failure_threshold = 3
        
        while True:
            try:
                # Check current active cloud
                is_failed, reason = self.detect_failure(self.current_active_cloud)
                
                if is_failed:
                    consecutive_failures[self.current_active_cloud] += 1
                    logger.warning(
                        f"{self.current_active_cloud.value} health check failed "
                        f"({consecutive_failures[self.current_active_cloud]}/{failure_threshold}): {reason}"
                    )
                    
                    if consecutive_failures[self.current_active_cloud] >= failure_threshold:
                        logger.error(f"{self.current_active_cloud.value} has failed!")
                        
                        # Determine next failover target
                        if self.current_active_cloud == CloudProvider.AWS:
                            target = CloudProvider.AZURE
                        elif self.current_active_cloud == CloudProvider.AZURE:
                            target = CloudProvider.GCP
                        else:
                            logger.critical("All clouds have failed! No failover target available.")
                            time.sleep(check_interval)
                            continue
                        
                        # Initiate failover
                        self.initiate_failover(target, reason)
                        
                        # Reset failure counters
                        consecutive_failures = {
                            CloudProvider.AWS: 0,
                            CloudProvider.AZURE: 0,
                            CloudProvider.GCP: 0
                        }
                else:
                    # Reset failure counter on success
                    consecutive_failures[self.current_active_cloud] = 0
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)


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
    
    parser = argparse.ArgumentParser(description='Failover Orchestration Service')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--target', choices=['aws', 'azure', 'gcp'], help='Target cloud for manual failover')
    parser.add_argument('--reason', default='Manual failover', help='Reason for manual failover')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=30, help='Health check interval in seconds')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize orchestrator
    orchestrator = FailoverOrchestrator(config)
    
    if args.monitor:
        # Start continuous monitoring
        orchestrator.monitor_and_failover(args.interval)
    elif args.target:
        # Manual failover
        target_map = {
            'aws': CloudProvider.AWS,
            'azure': CloudProvider.AZURE,
            'gcp': CloudProvider.GCP
        }
        target = target_map[args.target]
        
        event = orchestrator.initiate_failover(target, args.reason)
        
        if event.status == FailoverStatus.COMPLETED.value:
            print(f"Failover completed successfully in {event.duration:.2f} seconds")
            sys.exit(0)
        else:
            print(f"Failover failed: {event.status}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
