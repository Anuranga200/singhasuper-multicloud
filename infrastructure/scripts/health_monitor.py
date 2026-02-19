#!/usr/bin/env python3
"""
Health Monitor Service

Continuous health monitoring service for multi-cloud DR system.
Monitors HTTP endpoints and database connectivity across AWS, Azure, and GCP.

Features:
- HTTP/HTTPS endpoint health checks (30-second interval)
- Database connectivity checks (60-second interval)
- Tracks consecutive failures
- Sends alerts on failures
- Logs all health check results
- Provides health status API

Requirements:
- Access to all cloud endpoints
- Database credentials from secret managers
- SNS topic for alerts
"""

import sys
import time
import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import requests
import pymysql
import boto3
import json
import os
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Component type enumeration"""
    APPLICATION = "application"
    DATABASE = "database"
    LOAD_BALANCER = "load_balancer"


@dataclass
class HealthCheckResult:
    """Health check result data"""
    component_name: str
    component_type: ComponentType
    cloud_provider: str
    status: HealthStatus
    response_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class HealthCheckConfig:
    """Health check configuration"""
    name: str
    type: ComponentType
    cloud: str
    endpoint: str
    check_interval: int
    timeout: int
    failure_threshold: int


class HealthMonitor:
    """Monitors health of all system components"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.running = False
        self.check_threads = []
        
        # Health check results history (last 100 per component)
        self.health_history: Dict[str, deque] = {}
        
        # Current health status
        self.current_status: Dict[str, HealthCheckResult] = {}
        
        # AWS clients
        self.sns_client = boto3.client('sns', region_name=config['aws_region'])
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=config['aws_region'])
        
        # Alert tracking (to avoid duplicate alerts)
        self.alert_sent: Dict[str, datetime] = {}
        self.alert_cooldown = timedelta(minutes=5)
        
    def check_http_endpoint(self, config: HealthCheckConfig) -> HealthCheckResult:
        """
        Check HTTP/HTTPS endpoint health
        
        Args:
            config: Health check configuration
            
        Returns:
            HealthCheckResult
        """
        start_time = time.time()
        
        try:
            response = requests.get(
                config.endpoint,
                timeout=config.timeout,
                verify=True
            )
            
            response_time = time.time() - start_time
            
            # Check status code
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                error_message = None
                
                # Try to parse JSON response
                try:
                    data = response.json()
                    metadata = {
                        'status_code': response.status_code,
                        'response_data': data
                    }
                except:
                    metadata = {
                        'status_code': response.status_code
                    }
            else:
                status = HealthStatus.UNHEALTHY
                error_message = f"HTTP {response.status_code}"
                metadata = {
                    'status_code': response.status_code
                }
            
            # Calculate consecutive failures
            consecutive_failures = self._get_consecutive_failures(config.name, status)
            
            return HealthCheckResult(
                component_name=config.name,
                component_type=config.type,
                cloud_provider=config.cloud,
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                error_message=error_message,
                consecutive_failures=consecutive_failures,
                metadata=metadata
            )
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            consecutive_failures = self._get_consecutive_failures(config.name, HealthStatus.UNHEALTHY)
            
            return HealthCheckResult(
                component_name=config.name,
                component_type=config.type,
                cloud_provider=config.cloud,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                timestamp=datetime.now(),
                error_message="Request timeout",
                consecutive_failures=consecutive_failures
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            consecutive_failures = self._get_consecutive_failures(config.name, HealthStatus.UNHEALTHY)
            
            return HealthCheckResult(
                component_name=config.name,
                component_type=config.type,
                cloud_provider=config.cloud,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                timestamp=datetime.now(),
                error_message=str(e),
                consecutive_failures=consecutive_failures
            )
    
    def check_database_connectivity(self, config: HealthCheckConfig) -> HealthCheckResult:
        """
        Check database connectivity and replication lag
        
        Args:
            config: Health check configuration
            
        Returns:
            HealthCheckResult
        """
        start_time = time.time()
        
        try:
            # Parse database endpoint
            parts = config.endpoint.split(':')
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 3306
            
            # Get credentials
            username, password = self._get_database_credentials(config.cloud)
            
            # Connect to database
            connection = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                connect_timeout=config.timeout
            )
            
            # Execute simple query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            response_time = time.time() - start_time
            
            # Check replication lag if replica
            replication_lag = None
            if config.cloud != 'aws':  # Azure and GCP are replicas
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SHOW REPLICA STATUS")
                        replica_status = cursor.fetchone()
                        if replica_status:
                            # Seconds_Behind_Master is at index 32
                            replication_lag = replica_status[32]
                except:
                    pass
            
            connection.close()
            
            # Determine status based on replication lag
            if replication_lag is not None and replication_lag > 5:
                status = HealthStatus.DEGRADED
                error_message = f"High replication lag: {replication_lag}s"
            else:
                status = HealthStatus.HEALTHY
                error_message = None
            
            consecutive_failures = self._get_consecutive_failures(config.name, status)
            
            metadata = {
                'replication_lag': replication_lag,
                'connection_time': response_time
            }
            
            return HealthCheckResult(
                component_name=config.name,
                component_type=config.type,
                cloud_provider=config.cloud,
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                error_message=error_message,
                consecutive_failures=consecutive_failures,
                metadata=metadata
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            consecutive_failures = self._get_consecutive_failures(config.name, HealthStatus.UNHEALTHY)
            
            return HealthCheckResult(
                component_name=config.name,
                component_type=config.type,
                cloud_provider=config.cloud,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                timestamp=datetime.now(),
                error_message=str(e),
                consecutive_failures=consecutive_failures
            )
    
    def _get_consecutive_failures(self, component_name: str, current_status: HealthStatus) -> int:
        """Calculate consecutive failures for a component"""
        if component_name not in self.health_history:
            return 1 if current_status != HealthStatus.HEALTHY else 0
        
        history = self.health_history[component_name]
        if not history:
            return 1 if current_status != HealthStatus.HEALTHY else 0
        
        last_result = history[-1]
        
        if current_status != HealthStatus.HEALTHY:
            if last_result.status != HealthStatus.HEALTHY:
                return last_result.consecutive_failures + 1
            else:
                return 1
        else:
            return 0
    
    def _get_database_credentials(self, cloud: str) -> tuple:
        """Get database credentials from secret manager"""
        if cloud == 'aws':
            secrets_client = boto3.client('secretsmanager', region_name=self.config['aws_region'])
            response = secrets_client.get_secret_value(SecretId=self.config['secrets']['aws'])
            secret = json.loads(response['SecretString'])
            return secret['username'], secret['password']
        
        elif cloud == 'azure':
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.config['secrets']['azure_vault_url'], credential=credential)
            
            username_secret = client.get_secret(self.config['secrets']['azure_username'])
            password_secret = client.get_secret(self.config['secrets']['azure_password'])
            
            return username_secret.value, password_secret.value
        
        elif cloud == 'gcp':
            from google.cloud import secretmanager
            
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv('GCP_PROJECT_ID')
            
            username_name = f"projects/{project_id}/secrets/{self.config['secrets']['gcp_username']}/versions/latest"
            password_name = f"projects/{project_id}/secrets/{self.config['secrets']['gcp_password']}/versions/latest"
            
            username_response = client.access_secret_version(request={"name": username_name})
            password_response = client.access_secret_version(request={"name": password_name})
            
            return username_response.payload.data.decode('UTF-8'), password_response.payload.data.decode('UTF-8')
        
        return "", ""
    
    def record_result(self, result: HealthCheckResult):
        """Record health check result"""
        # Initialize history if needed
        if result.component_name not in self.health_history:
            self.health_history[result.component_name] = deque(maxlen=100)
        
        # Add to history
        self.health_history[result.component_name].append(result)
        
        # Update current status
        self.current_status[result.component_name] = result
        
        # Log result
        status_symbol = "✓" if result.status == HealthStatus.HEALTHY else "✗"
        logger.info(
            f"{status_symbol} {result.component_name} ({result.cloud_provider}): "
            f"{result.status.value} - {result.response_time:.3f}s"
        )
        
        if result.error_message:
            logger.warning(f"  Error: {result.error_message}")
        
        # Send metrics to CloudWatch
        self.send_metrics(result)
        
        # Check if alert needed
        if result.consecutive_failures >= result.component_name in self.config.get('failure_threshold', 3):
            self.send_alert(result)
    
    def send_metrics(self, result: HealthCheckResult):
        """Send metrics to CloudWatch"""
        try:
            metric_data = [
                {
                    'MetricName': 'HealthCheckStatus',
                    'Value': 1 if result.status == HealthStatus.HEALTHY else 0,
                    'Unit': 'None',
                    'Timestamp': result.timestamp,
                    'Dimensions': [
                        {'Name': 'Component', 'Value': result.component_name},
                        {'Name': 'Cloud', 'Value': result.cloud_provider},
                        {'Name': 'Type', 'Value': result.component_type.value}
                    ]
                },
                {
                    'MetricName': 'ResponseTime',
                    'Value': result.response_time,
                    'Unit': 'Seconds',
                    'Timestamp': result.timestamp,
                    'Dimensions': [
                        {'Name': 'Component', 'Value': result.component_name},
                        {'Name': 'Cloud', 'Value': result.cloud_provider}
                    ]
                }
            ]
            
            # Add replication lag metric if available
            if 'replication_lag' in result.metadata and result.metadata['replication_lag'] is not None:
                metric_data.append({
                    'MetricName': 'ReplicationLag',
                    'Value': result.metadata['replication_lag'],
                    'Unit': 'Seconds',
                    'Timestamp': result.timestamp,
                    'Dimensions': [
                        {'Name': 'Component', 'Value': result.component_name},
                        {'Name': 'Cloud', 'Value': result.cloud_provider}
                    ]
                })
            
            self.cloudwatch_client.put_metric_data(
                Namespace='MultiCloudDR/HealthMonitor',
                MetricData=metric_data
            )
            
        except Exception as e:
            logger.error(f"Error sending metrics: {e}")
    
    def send_alert(self, result: HealthCheckResult):
        """Send alert for unhealthy component"""
        # Check cooldown
        if result.component_name in self.alert_sent:
            last_alert = self.alert_sent[result.component_name]
            if datetime.now() - last_alert < self.alert_cooldown:
                return  # Skip alert due to cooldown
        
        try:
            subject = f"⚠ Health Alert: {result.component_name} ({result.cloud_provider})"
            
            message = f"""
Multi-Cloud DR System Health Alert

Component: {result.component_name}
Cloud: {result.cloud_provider}
Type: {result.component_type.value}
Status: {result.status.value}
Consecutive Failures: {result.consecutive_failures}

Timestamp: {result.timestamp.isoformat()}
Response Time: {result.response_time:.3f}s

Error: {result.error_message or 'N/A'}

Metadata: {json.dumps(result.metadata, indent=2)}

---
This is an automated alert from the Health Monitor Service.
"""
            
            self.sns_client.publish(
                TopicArn=self.config['sns_topic_arn'],
                Subject=subject,
                Message=message
            )
            
            self.alert_sent[result.component_name] = datetime.now()
            logger.info(f"Alert sent for {result.component_name}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def monitor_component(self, config: HealthCheckConfig):
        """Monitor a single component continuously"""
        logger.info(f"Starting monitor for {config.name} (interval: {config.check_interval}s)")
        
        while self.running:
            try:
                # Perform health check
                if config.type == ComponentType.APPLICATION or config.type == ComponentType.LOAD_BALANCER:
                    result = self.check_http_endpoint(config)
                elif config.type == ComponentType.DATABASE:
                    result = self.check_database_connectivity(config)
                else:
                    logger.error(f"Unknown component type: {config.type}")
                    time.sleep(config.check_interval)
                    continue
                
                # Record result
                self.record_result(result)
                
                # Wait for next check
                time.sleep(config.check_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring {config.name}: {e}")
                time.sleep(config.check_interval)
    
    def start(self):
        """Start health monitoring"""
        logger.info("Starting Health Monitor Service...")
        self.running = True
        
        # Create health check configurations
        checks = self._create_health_check_configs()
        
        # Start monitoring thread for each component
        for check_config in checks:
            thread = threading.Thread(
                target=self.monitor_component,
                args=(check_config,),
                daemon=True
            )
            thread.start()
            self.check_threads.append(thread)
        
        logger.info(f"Started {len(self.check_threads)} health check threads")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()
    
    def stop(self):
        """Stop health monitoring"""
        logger.info("Stopping Health Monitor Service...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.check_threads:
            thread.join(timeout=5)
        
        logger.info("Health Monitor Service stopped")
    
    def _create_health_check_configs(self) -> List[HealthCheckConfig]:
        """Create health check configurations from config"""
        configs = []
        
        # Application endpoints (30-second interval)
        for cloud in ['aws', 'azure', 'gcp']:
            if cloud in self.config['endpoints']:
                endpoint_config = self.config['endpoints'][cloud]
                
                configs.append(HealthCheckConfig(
                    name=f"{cloud}-application",
                    type=ComponentType.APPLICATION,
                    cloud=cloud,
                    endpoint=endpoint_config['app_url'],
                    check_interval=30,
                    timeout=10,
                    failure_threshold=3
                ))
        
        # Database endpoints (60-second interval)
        for cloud in ['aws', 'azure', 'gcp']:
            if cloud in self.config['databases']:
                db_config = self.config['databases'][cloud]
                
                configs.append(HealthCheckConfig(
                    name=f"{cloud}-database",
                    type=ComponentType.DATABASE,
                    cloud=cloud,
                    endpoint=db_config['endpoint'],
                    check_interval=60,
                    timeout=10,
                    failure_threshold=3
                ))
        
        return configs
    
    def get_health_summary(self) -> Dict:
        """Get current health summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        unhealthy_count = 0
        
        for name, result in self.current_status.items():
            summary['components'][name] = {
                'status': result.status.value,
                'cloud': result.cloud_provider,
                'type': result.component_type.value,
                'response_time': result.response_time,
                'consecutive_failures': result.consecutive_failures,
                'last_check': result.timestamp.isoformat()
            }
            
            if result.status != HealthStatus.HEALTHY:
                unhealthy_count += 1
        
        if unhealthy_count > 0:
            summary['overall_status'] = 'degraded' if unhealthy_count < len(self.current_status) else 'unhealthy'
        
        return summary


def load_config() -> Dict:
    """Load configuration from environment variables"""
    return {
        'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
        'sns_topic_arn': os.getenv('SNS_TOPIC_ARN'),
        'failure_threshold': int(os.getenv('FAILURE_THRESHOLD', '3')),
        'endpoints': {
            'aws': {
                'app_url': os.getenv('AWS_APP_URL', 'https://aws-endpoint.example.com/health')
            },
            'azure': {
                'app_url': os.getenv('AZURE_APP_URL', 'https://azure-endpoint.example.com/health')
            },
            'gcp': {
                'app_url': os.getenv('GCP_APP_URL', 'https://gcp-endpoint.example.com/health')
            }
        },
        'databases': {
            'aws': {
                'endpoint': os.getenv('AWS_DB_ENDPOINT', 'aws-db.example.com:3306')
            },
            'azure': {
                'endpoint': os.getenv('AZURE_DB_ENDPOINT', 'azure-db.example.com:3306')
            },
            'gcp': {
                'endpoint': os.getenv('GCP_DB_ENDPOINT', 'gcp-db.example.com:3306')
            }
        },
        'secrets': {
            'aws': os.getenv('AWS_SECRET_NAME', 'db-credentials'),
            'azure_vault_url': os.getenv('AZURE_KEY_VAULT_URL'),
            'azure_username': os.getenv('AZURE_USERNAME_SECRET', 'db-username'),
            'azure_password': os.getenv('AZURE_PASSWORD_SECRET', 'db-password'),
            'gcp_username': os.getenv('GCP_USERNAME_SECRET', 'db-username'),
            'gcp_password': os.getenv('GCP_PASSWORD_SECRET', 'db-password')
        }
    }


def main():
    """Main execution flow"""
    logger.info("Initializing Health Monitor Service...")
    
    config = load_config()
    
    # Validate configuration
    if not config['sns_topic_arn']:
        logger.error("SNS_TOPIC_ARN environment variable not set")
        sys.exit(1)
    
    monitor = HealthMonitor(config)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        monitor.stop()


if __name__ == '__main__':
    main()
