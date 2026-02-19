#!/usr/bin/env python3
"""
DNS Failover Orchestration Script

This script monitors Route 53 health check status and orchestrates DNS failover
when failures are detected. It implements the failover cascade: AWS → Azure → GCP.

Features:
- Monitors health check status from Route 53
- Triggers DNS record updates on failures
- Logs failover events with timestamps
- Sends notifications via SNS
- Implements failover cascade logic

Requirements:
- AWS credentials with Route 53 and SNS permissions
- Route 53 hosted zone configured
- Health checks configured for all clouds
"""

import sys
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import boto3
import json
import os

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


class HealthStatus(Enum):
    """Health check status enumeration"""
    HEALTHY = "Healthy"
    UNHEALTHY = "Unhealthy"
    UNKNOWN = "Unknown"


@dataclass
class HealthCheckResult:
    """Health check result data"""
    cloud: CloudProvider
    status: HealthStatus
    check_id: str
    timestamp: datetime
    consecutive_failures: int = 0


@dataclass
class FailoverEvent:
    """Failover event data"""
    event_id: str
    timestamp: datetime
    source_cloud: CloudProvider
    target_cloud: CloudProvider
    reason: str
    duration: Optional[float] = None
    success: bool = False


class DNSFailoverOrchestrator:
    """Orchestrates DNS failover based on health check status"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.route53_client = boto3.client('route53', region_name=config['aws_region'])
        self.sns_client = boto3.client('sns', region_name=config['aws_region'])
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=config['aws_region'])
        
        self.current_active_cloud = CloudProvider.AWS
        self.health_history: Dict[CloudProvider, List[HealthCheckResult]] = {
            CloudProvider.AWS: [],
            CloudProvider.AZURE: [],
            CloudProvider.GCP: []
        }
        self.failover_events: List[FailoverEvent] = []
        
    def get_health_check_status(self, health_check_id: str) -> HealthStatus:
        """
        Get current status of a Route 53 health check
        
        Args:
            health_check_id: Route 53 health check ID
            
        Returns:
            HealthStatus enum value
        """
        try:
            response = self.route53_client.get_health_check_status(
                HealthCheckId=health_check_id
            )
            
            if not response['HealthCheckObservations']:
                return HealthStatus.UNKNOWN
            
            # Check if majority of checkers report healthy
            healthy_count = sum(
                1 for obs in response['HealthCheckObservations']
                if obs['StatusReport']['Status'] == 'Success'
            )
            total_count = len(response['HealthCheckObservations'])
            
            if healthy_count / total_count >= 0.5:
                return HealthStatus.HEALTHY
            else:
                return HealthStatus.UNHEALTHY
                
        except Exception as e:
            logger.error(f"Error getting health check status: {e}")
            return HealthStatus.UNKNOWN
    
    def check_all_health_statuses(self) -> Dict[CloudProvider, HealthCheckResult]:
        """
        Check health status for all clouds
        
        Returns:
            Dictionary mapping cloud providers to health check results
        """
        results = {}
        
        for cloud, check_id in [
            (CloudProvider.AWS, self.config['health_checks']['aws']),
            (CloudProvider.AZURE, self.config['health_checks']['azure']),
            (CloudProvider.GCP, self.config['health_checks']['gcp'])
        ]:
            status = self.get_health_check_status(check_id)
            
            # Calculate consecutive failures
            consecutive_failures = 0
            if self.health_history[cloud]:
                last_result = self.health_history[cloud][-1]
                if status == HealthStatus.UNHEALTHY:
                    consecutive_failures = last_result.consecutive_failures + 1
            elif status == HealthStatus.UNHEALTHY:
                consecutive_failures = 1
            
            result = HealthCheckResult(
                cloud=cloud,
                status=status,
                check_id=check_id,
                timestamp=datetime.now(),
                consecutive_failures=consecutive_failures
            )
            
            results[cloud] = result
            self.health_history[cloud].append(result)
            
            # Keep only last 100 results
            if len(self.health_history[cloud]) > 100:
                self.health_history[cloud] = self.health_history[cloud][-100:]
        
        return results
    
    def should_trigger_failover(self, results: Dict[CloudProvider, HealthCheckResult]) -> Tuple[bool, Optional[CloudProvider]]:
        """
        Determine if failover should be triggered
        
        Args:
            results: Current health check results
            
        Returns:
            Tuple of (should_failover, target_cloud)
        """
        current_result = results[self.current_active_cloud]
        
        # Check if current active cloud is unhealthy
        if current_result.status != HealthStatus.HEALTHY:
            # Check consecutive failures threshold
            if current_result.consecutive_failures >= self.config['failure_threshold']:
                logger.warning(
                    f"{self.current_active_cloud.value} has {current_result.consecutive_failures} "
                    f"consecutive failures. Triggering failover."
                )
                
                # Determine target cloud based on priority
                if self.current_active_cloud == CloudProvider.AWS:
                    # Try Azure first
                    if results[CloudProvider.AZURE].status == HealthStatus.HEALTHY:
                        return True, CloudProvider.AZURE
                    # Fall back to GCP
                    elif results[CloudProvider.GCP].status == HealthStatus.HEALTHY:
                        return True, CloudProvider.GCP
                    else:
                        logger.error("No healthy failover target available!")
                        return False, None
                
                elif self.current_active_cloud == CloudProvider.AZURE:
                    # Try GCP
                    if results[CloudProvider.GCP].status == HealthStatus.HEALTHY:
                        return True, CloudProvider.GCP
                    # Try AWS (failback)
                    elif results[CloudProvider.AWS].status == HealthStatus.HEALTHY:
                        return True, CloudProvider.AWS
                    else:
                        logger.error("No healthy failover target available!")
                        return False, None
                
                elif self.current_active_cloud == CloudProvider.GCP:
                    # Try AWS (failback)
                    if results[CloudProvider.AWS].status == HealthStatus.HEALTHY:
                        return True, CloudProvider.AWS
                    # Try Azure
                    elif results[CloudProvider.AZURE].status == HealthStatus.HEALTHY:
                        return True, CloudProvider.AZURE
                    else:
                        logger.error("No healthy failover target available!")
                        return False, None
        
        return False, None
    
    def update_dns_records(self, target_cloud: CloudProvider) -> bool:
        """
        Update DNS records to point to target cloud
        
        Args:
            target_cloud: Target cloud provider
            
        Returns:
            True if successful, False otherwise
        """
        try:
            zone_id = self.config['hosted_zone_id']
            domain_name = self.config['domain_name']
            
            # Get target IP address
            target_ip = self.config['endpoints'][target_cloud.value.lower()]['ip']
            
            # Update DNS record
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    'Comment': f'Failover to {target_cloud.value} at {datetime.now().isoformat()}',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': domain_name,
                                'Type': 'A',
                                'TTL': self.config['dns_ttl'],
                                'ResourceRecords': [{'Value': target_ip}]
                            }
                        }
                    ]
                }
            )
            
            change_id = response['ChangeInfo']['Id']
            logger.info(f"DNS update initiated. Change ID: {change_id}")
            
            # Wait for change to propagate
            waiter = self.route53_client.get_waiter('resource_record_sets_changed')
            waiter.wait(Id=change_id, WaiterConfig={'Delay': 5, 'MaxAttempts': 12})
            
            logger.info(f"DNS records updated successfully to {target_cloud.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating DNS records: {e}")
            return False
    
    def execute_failover(self, target_cloud: CloudProvider, reason: str) -> FailoverEvent:
        """
        Execute failover to target cloud
        
        Args:
            target_cloud: Target cloud provider
            reason: Reason for failover
            
        Returns:
            FailoverEvent with results
        """
        event_id = f"failover-{int(time.time())}"
        start_time = time.time()
        
        logger.info(f"Executing failover from {self.current_active_cloud.value} to {target_cloud.value}")
        logger.info(f"Reason: {reason}")
        
        event = FailoverEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            source_cloud=self.current_active_cloud,
            target_cloud=target_cloud,
            reason=reason
        )
        
        # Update DNS records
        if self.update_dns_records(target_cloud):
            duration = time.time() - start_time
            event.duration = duration
            event.success = True
            
            # Update current active cloud
            self.current_active_cloud = target_cloud
            
            logger.info(f"Failover completed successfully in {duration:.2f} seconds")
            
            # Send notification
            self.send_failover_notification(event)
            
            # Log event
            self.log_failover_event(event)
        else:
            duration = time.time() - start_time
            event.duration = duration
            event.success = False
            
            logger.error(f"Failover failed after {duration:.2f} seconds")
            
            # Send failure notification
            self.send_failover_notification(event)
        
        self.failover_events.append(event)
        return event
    
    def send_failover_notification(self, event: FailoverEvent):
        """Send SNS notification about failover event"""
        try:
            subject = f"{'✓' if event.success else '✗'} Failover: {event.source_cloud.value} → {event.target_cloud.value}"
            
            message = f"""
Multi-Cloud DR System Failover Event

Event ID: {event.event_id}
Timestamp: {event.timestamp.isoformat()}
Status: {'SUCCESS' if event.success else 'FAILED'}

Source Cloud: {event.source_cloud.value}
Target Cloud: {event.target_cloud.value}
Reason: {event.reason}
Duration: {event.duration:.2f} seconds

Current Active Cloud: {self.current_active_cloud.value}

---
This is an automated notification from the Multi-Cloud DR System.
"""
            
            self.sns_client.publish(
                TopicArn=self.config['sns_topic_arn'],
                Subject=subject,
                Message=message
            )
            
            logger.info("Failover notification sent")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def log_failover_event(self, event: FailoverEvent):
        """Log failover event to CloudWatch"""
        try:
            self.cloudwatch_client.put_metric_data(
                Namespace='MultiCloudDR',
                MetricData=[
                    {
                        'MetricName': 'FailoverEvent',
                        'Value': 1 if event.success else 0,
                        'Unit': 'Count',
                        'Timestamp': event.timestamp,
                        'Dimensions': [
                            {'Name': 'SourceCloud', 'Value': event.source_cloud.value},
                            {'Name': 'TargetCloud', 'Value': event.target_cloud.value}
                        ]
                    },
                    {
                        'MetricName': 'FailoverDuration',
                        'Value': event.duration,
                        'Unit': 'Seconds',
                        'Timestamp': event.timestamp,
                        'Dimensions': [
                            {'Name': 'SourceCloud', 'Value': event.source_cloud.value},
                            {'Name': 'TargetCloud', 'Value': event.target_cloud.value}
                        ]
                    }
                ]
            )
            
            logger.info("Failover event logged to CloudWatch")
            
        except Exception as e:
            logger.error(f"Error logging to CloudWatch: {e}")
    
    def monitor_and_orchestrate(self, interval: int = 30, duration: Optional[int] = None):
        """
        Monitor health checks and orchestrate failover
        
        Args:
            interval: Check interval in seconds
            duration: Total duration to monitor in seconds (None for infinite)
        """
        logger.info(f"Starting DNS failover orchestration (interval: {interval}s)")
        
        start_time = time.time()
        
        while True:
            try:
                # Check health statuses
                results = self.check_all_health_statuses()
                
                # Log current status
                logger.info("Health Check Status:")
                for cloud, result in results.items():
                    logger.info(f"  {cloud.value}: {result.status.value} (failures: {result.consecutive_failures})")
                
                # Check if failover needed
                should_failover, target_cloud = self.should_trigger_failover(results)
                
                if should_failover and target_cloud:
                    reason = f"{self.current_active_cloud.value} unhealthy ({results[self.current_active_cloud].consecutive_failures} consecutive failures)"
                    self.execute_failover(target_cloud, reason)
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    logger.info("Monitoring duration reached. Exiting.")
                    break
                
                # Wait for next check
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def print_summary(self):
        """Print summary of failover events"""
        print("\n" + "="*80)
        print("DNS FAILOVER ORCHESTRATION SUMMARY")
        print("="*80)
        print(f"Current Active Cloud: {self.current_active_cloud.value}")
        print(f"Total Failover Events: {len(self.failover_events)}")
        
        if self.failover_events:
            print("\nFailover Events:")
            for event in self.failover_events:
                status = "✓ SUCCESS" if event.success else "✗ FAILED"
                print(f"\n  {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {status}")
                print(f"    {event.source_cloud.value} → {event.target_cloud.value}")
                print(f"    Reason: {event.reason}")
                print(f"    Duration: {event.duration:.2f}s")
        
        print("="*80 + "\n")


def load_config() -> Dict:
    """Load configuration from environment variables"""
    return {
        'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
        'hosted_zone_id': os.getenv('HOSTED_ZONE_ID'),
        'domain_name': os.getenv('DOMAIN_NAME'),
        'dns_ttl': int(os.getenv('DNS_TTL', '60')),
        'failure_threshold': int(os.getenv('FAILURE_THRESHOLD', '3')),
        'sns_topic_arn': os.getenv('SNS_TOPIC_ARN'),
        'health_checks': {
            'aws': os.getenv('AWS_HEALTH_CHECK_ID'),
            'azure': os.getenv('AZURE_HEALTH_CHECK_ID'),
            'gcp': os.getenv('GCP_HEALTH_CHECK_ID')
        },
        'endpoints': {
            'aws': {
                'ip': os.getenv('AWS_IP_ADDRESS'),
                'fqdn': os.getenv('AWS_ENDPOINT')
            },
            'azure': {
                'ip': os.getenv('AZURE_IP_ADDRESS'),
                'fqdn': os.getenv('AZURE_ENDPOINT')
            },
            'gcp': {
                'ip': os.getenv('GCP_IP_ADDRESS'),
                'fqdn': os.getenv('GCP_ENDPOINT')
            }
        }
    }


def main():
    """Main execution flow"""
    logger.info("Starting DNS Failover Orchestrator...")
    
    config = load_config()
    
    # Validate configuration
    if not config['hosted_zone_id']:
        logger.error("HOSTED_ZONE_ID environment variable not set")
        sys.exit(1)
    
    if not config['sns_topic_arn']:
        logger.error("SNS_TOPIC_ARN environment variable not set")
        sys.exit(1)
    
    orchestrator = DNSFailoverOrchestrator(config)
    
    try:
        # Monitor and orchestrate failover
        orchestrator.monitor_and_orchestrate(interval=30)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        orchestrator.print_summary()


if __name__ == '__main__':
    main()
