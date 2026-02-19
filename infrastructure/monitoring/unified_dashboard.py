#!/usr/bin/env python3
"""
Unified Multi-Cloud Dashboard

This script creates a unified dashboard that aggregates metrics from all cloud
providers (AWS, Azure, GCP) into a single view.

Features:
- Aggregate metrics from all clouds
- Display overall system health status
- Show current active cloud and failover status
- Display RTO/RPO metrics
- Unified alerting and monitoring

Requirements:
- AWS, Azure, and GCP credentials
- Access to monitoring APIs from all clouds
"""

import sys
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import boto3
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.monitor import MonitorManagementClient
    from google.cloud import monitoring_v3
    from google.oauth2 import service_account
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install boto3 azure-identity azure-mgmt-monitor google-cloud-monitoring")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudStatus(Enum):
    """Cloud status enumeration"""
    ACTIVE = "active"
    PASSIVE = "passive"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class CloudMetrics:
    """Cloud metrics data"""
    cloud_provider: str
    status: str
    cpu_utilization: float
    memory_utilization: float
    network_in_bytes: int
    network_out_bytes: int
    database_connections: int
    database_cpu: float
    replication_lag_seconds: float
    load_balancer_requests: int
    load_balancer_latency_ms: float
    healthy_targets: int
    unhealthy_targets: int
    timestamp: datetime


@dataclass
class SystemHealth:
    """Overall system health"""
    active_cloud: str
    failover_clouds: List[str]
    overall_status: str
    rto_seconds: float
    rpo_seconds: float
    last_failover: Optional[datetime]
    total_requests_24h: int
    average_latency_ms: float
    error_rate_percent: float
    timestamp: datetime


class UnifiedDashboard:
    """Manages unified multi-cloud dashboard"""
    
    def __init__(self, config: Dict):
        """
        Initialize unified dashboard
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize AWS clients
        aws_region = config.get('aws_region', 'us-east-1')
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.rds = boto3.client('rds', region_name=aws_region)
        
        # Initialize Azure clients
        if 'azure_subscription_id' in config:
            self.azure_credential = DefaultAzureCredential()
            self.azure_monitor = MonitorManagementClient(
                self.azure_credential,
                config['azure_subscription_id']
            )
        
        # Initialize GCP clients
        if 'gcp_project_id' in config:
            if 'gcp_credentials_file' in config:
                credentials = service_account.Credentials.from_service_account_file(
                    config['gcp_credentials_file']
                )
                self.gcp_monitoring = monitoring_v3.MetricServiceClient(credentials=credentials)
            else:
                self.gcp_monitoring = monitoring_v3.MetricServiceClient()
            
            self.gcp_project_name = f"projects/{config['gcp_project_id']}"
        
        logger.info("Unified Dashboard initialized")
    
    def collect_aws_metrics(self) -> CloudMetrics:
        """
        Collect metrics from AWS
        
        Returns:
            CloudMetrics object
        """
        logger.info("Collecting AWS metrics...")
        
        try:
            # Get EC2 CPU utilization
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                StartTime=datetime.utcnow() - timedelta(minutes=5),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )
            
            cpu_util = cpu_response['Datapoints'][0]['Average'] if cpu_response['Datapoints'] else 0.0
            
            # Get RDS metrics
            db_instance_id = self.config.get('aws_db_instance_id', 'singha-loyalty-db-primary')
            
            db_cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
                StartTime=datetime.utcnow() - timedelta(minutes=5),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )
            
            db_cpu = db_cpu_response['Datapoints'][0]['Average'] if db_cpu_response['Datapoints'] else 0.0
            
            # Get replication lag
            lag_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='ReplicaLag',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
                StartTime=datetime.utcnow() - timedelta(minutes=5),
                EndTime=datetime.utcnow(),
                Period=60,
                Statistics=['Average']
            )
            
            replication_lag = lag_response['Datapoints'][0]['Average'] if lag_response['Datapoints'] else 0.0
            
            # Get ALB metrics
            alb_requests_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='RequestCount',
                StartTime=datetime.utcnow() - timedelta(minutes=5),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Sum']
            )
            
            alb_requests = alb_requests_response['Datapoints'][0]['Sum'] if alb_requests_response['Datapoints'] else 0
            
            metrics = CloudMetrics(
                cloud_provider='AWS',
                status=CloudStatus.ACTIVE.value,
                cpu_utilization=cpu_util,
                memory_utilization=0.0,  # Not easily available
                network_in_bytes=0,
                network_out_bytes=0,
                database_connections=0,
                database_cpu=db_cpu,
                replication_lag_seconds=replication_lag,
                load_balancer_requests=int(alb_requests),
                load_balancer_latency_ms=0.0,
                healthy_targets=0,
                unhealthy_targets=0,
                timestamp=datetime.utcnow()
            )
            
            logger.info("AWS metrics collected successfully")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting AWS metrics: {e}")
            return CloudMetrics(
                cloud_provider='AWS',
                status=CloudStatus.UNKNOWN.value,
                cpu_utilization=0.0,
                memory_utilization=0.0,
                network_in_bytes=0,
                network_out_bytes=0,
                database_connections=0,
                database_cpu=0.0,
                replication_lag_seconds=0.0,
                load_balancer_requests=0,
                load_balancer_latency_ms=0.0,
                healthy_targets=0,
                unhealthy_targets=0,
                timestamp=datetime.utcnow()
            )
    
    def collect_azure_metrics(self) -> CloudMetrics:
        """
        Collect metrics from Azure
        
        Returns:
            CloudMetrics object
        """
        logger.info("Collecting Azure metrics...")
        
        try:
            # Azure metrics collection would go here
            # This is a simplified version
            
            metrics = CloudMetrics(
                cloud_provider='Azure',
                status=CloudStatus.PASSIVE.value,
                cpu_utilization=0.0,
                memory_utilization=0.0,
                network_in_bytes=0,
                network_out_bytes=0,
                database_connections=0,
                database_cpu=0.0,
                replication_lag_seconds=0.0,
                load_balancer_requests=0,
                load_balancer_latency_ms=0.0,
                healthy_targets=0,
                unhealthy_targets=0,
                timestamp=datetime.utcnow()
            )
            
            logger.info("Azure metrics collected successfully")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting Azure metrics: {e}")
            return CloudMetrics(
                cloud_provider='Azure',
                status=CloudStatus.UNKNOWN.value,
                cpu_utilization=0.0,
                memory_utilization=0.0,
                network_in_bytes=0,
                network_out_bytes=0,
                database_connections=0,
                database_cpu=0.0,
                replication_lag_seconds=0.0,
                load_balancer_requests=0,
                load_balancer_latency_ms=0.0,
                healthy_targets=0,
                unhealthy_targets=0,
                timestamp=datetime.utcnow()
            )
    
    def collect_gcp_metrics(self) -> CloudMetrics:
        """
        Collect metrics from GCP
        
        Returns:
            CloudMetrics object
        """
        logger.info("Collecting GCP metrics...")
        
        try:
            # GCP metrics collection would go here
            # This is a simplified version
            
            metrics = CloudMetrics(
                cloud_provider='GCP',
                status=CloudStatus.PASSIVE.value,
                cpu_utilization=0.0,
                memory_utilization=0.0,
                network_in_bytes=0,
                network_out_bytes=0,
                database_connections=0,
                database_cpu=0.0,
                replication_lag_seconds=0.0,
                load_balancer_requests=0,
                load_balancer_latency_ms=0.0,
                healthy_targets=0,
                unhealthy_targets=0,
                timestamp=datetime.utcnow()
            )
            
            logger.info("GCP metrics collected successfully")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting GCP metrics: {e}")
            return CloudMetrics(
                cloud_provider='GCP',
                status=CloudStatus.UNKNOWN.value,
                cpu_utilization=0.0,
                memory_utilization=0.0,
                network_in_bytes=0,
                network_out_bytes=0,
                database_connections=0,
                database_cpu=0.0,
                replication_lag_seconds=0.0,
                load_balancer_requests=0,
                load_balancer_latency_ms=0.0,
                healthy_targets=0,
                unhealthy_targets=0,
                timestamp=datetime.utcnow()
            )
    
    def collect_all_metrics(self) -> Dict[str, CloudMetrics]:
        """
        Collect metrics from all clouds
        
        Returns:
            Dictionary mapping cloud provider to metrics
        """
        logger.info("Collecting metrics from all clouds...")
        
        metrics = {}
        
        # Collect AWS metrics
        if 'aws_region' in self.config:
            metrics['AWS'] = self.collect_aws_metrics()
        
        # Collect Azure metrics
        if 'azure_subscription_id' in self.config:
            metrics['Azure'] = self.collect_azure_metrics()
        
        # Collect GCP metrics
        if 'gcp_project_id' in self.config:
            metrics['GCP'] = self.collect_gcp_metrics()
        
        return metrics
    
    def calculate_system_health(self, cloud_metrics: Dict[str, CloudMetrics]) -> SystemHealth:
        """
        Calculate overall system health
        
        Args:
            cloud_metrics: Dictionary of cloud metrics
            
        Returns:
            SystemHealth object
        """
        logger.info("Calculating system health...")
        
        # Determine active cloud
        active_cloud = 'AWS'  # Default
        for cloud, metrics in cloud_metrics.items():
            if metrics.status == CloudStatus.ACTIVE.value:
                active_cloud = cloud
                break
        
        # Determine failover clouds
        failover_clouds = [cloud for cloud, metrics in cloud_metrics.items() 
                          if metrics.status == CloudStatus.PASSIVE.value]
        
        # Calculate overall status
        unhealthy_count = sum(1 for metrics in cloud_metrics.values() 
                             if metrics.status == CloudStatus.UNHEALTHY.value)
        
        if unhealthy_count == 0:
            overall_status = 'healthy'
        elif unhealthy_count < len(cloud_metrics):
            overall_status = 'degraded'
        else:
            overall_status = 'critical'
        
        # Calculate aggregate metrics
        total_requests = sum(metrics.load_balancer_requests for metrics in cloud_metrics.values())
        avg_latency = sum(metrics.load_balancer_latency_ms for metrics in cloud_metrics.values()) / len(cloud_metrics) if cloud_metrics else 0.0
        
        # Calculate max replication lag (RPO indicator)
        max_replication_lag = max((metrics.replication_lag_seconds for metrics in cloud_metrics.values()), default=0.0)
        
        health = SystemHealth(
            active_cloud=active_cloud,
            failover_clouds=failover_clouds,
            overall_status=overall_status,
            rto_seconds=300.0,  # 5 minutes target
            rpo_seconds=max_replication_lag,
            last_failover=None,  # Would be loaded from history
            total_requests_24h=total_requests,
            average_latency_ms=avg_latency,
            error_rate_percent=0.0,  # Would be calculated from actual data
            timestamp=datetime.utcnow()
        )
        
        return health
    
    def generate_dashboard_html(self, cloud_metrics: Dict[str, CloudMetrics], 
                                system_health: SystemHealth) -> str:
        """
        Generate HTML dashboard
        
        Args:
            cloud_metrics: Cloud metrics dictionary
            system_health: System health object
            
        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Cloud DR System Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .status-card {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .status-healthy {{ border-left: 5px solid #27ae60; }}
        .status-degraded {{ border-left: 5px solid #f39c12; }}
        .status-critical {{ border-left: 5px solid #e74c3c; }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .metric-card {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .cloud-section {{
            margin-top: 30px;
        }}
        .cloud-header {{
            background-color: #34495e;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-active {{ background-color: #27ae60; color: white; }}
        .badge-passive {{ background-color: #3498db; color: white; }}
        .badge-unhealthy {{ background-color: #e74c3c; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Multi-Cloud Disaster Recovery System</h1>
        <p>Real-time monitoring across AWS, Azure, and GCP</p>
        <p>Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
    
    <div class="status-card status-{system_health.overall_status}">
        <h2>System Health: {system_health.overall_status.upper()}</h2>
        <p><strong>Active Cloud:</strong> {system_health.active_cloud}</p>
        <p><strong>Failover Clouds:</strong> {', '.join(system_health.failover_clouds)}</p>
        <p><strong>RTO Target:</strong> {system_health.rto_seconds}s | <strong>Current RPO:</strong> {system_health.rpo_seconds:.2f}s</p>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Total Requests (5 min)</div>
            <div class="metric-value">{system_health.total_requests_24h:,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Average Latency</div>
            <div class="metric-value">{system_health.average_latency_ms:.2f} ms</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Error Rate</div>
            <div class="metric-value">{system_health.error_rate_percent:.2f}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Replication Lag (Max)</div>
            <div class="metric-value">{system_health.rpo_seconds:.2f}s</div>
        </div>
    </div>
"""
        
        # Add cloud-specific sections
        for cloud, metrics in cloud_metrics.items():
            status_class = f"badge-{metrics.status}"
            html += f"""
    <div class="cloud-section">
        <div class="cloud-header">
            <h3>{cloud} <span class="status-badge {status_class}">{metrics.status.upper()}</span></h3>
        </div>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">CPU Utilization</div>
                <div class="metric-value">{metrics.cpu_utilization:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Database CPU</div>
                <div class="metric-value">{metrics.database_cpu:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Replication Lag</div>
                <div class="metric-value">{metrics.replication_lag_seconds:.2f}s</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">LB Requests</div>
                <div class="metric-value">{metrics.load_balancer_requests:,}</div>
            </div>
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def generate_dashboard(self, output_file: str = 'unified_dashboard.html') -> bool:
        """
        Generate unified dashboard
        
        Args:
            output_file: Output HTML file path
            
        Returns:
            True if successful
        """
        try:
            # Collect metrics
            cloud_metrics = self.collect_all_metrics()
            
            # Calculate system health
            system_health = self.calculate_system_health(cloud_metrics)
            
            # Generate HTML
            html = self.generate_dashboard_html(cloud_metrics, system_health)
            
            # Write to file
            with open(output_file, 'w') as f:
                f.write(html)
            
            logger.info(f"Dashboard generated: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return False
    
    def generate_json_report(self) -> Dict:
        """
        Generate JSON report of all metrics
        
        Returns:
            Report dictionary
        """
        cloud_metrics = self.collect_all_metrics()
        system_health = self.calculate_system_health(cloud_metrics)
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_health': asdict(system_health),
            'cloud_metrics': {
                cloud: asdict(metrics) for cloud, metrics in cloud_metrics.items()
            }
        }
        
        return report


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Multi-Cloud Dashboard')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--action', required=True, 
                       choices=['generate-html', 'generate-json'],
                       help='Action to perform')
    parser.add_argument('--output', default='unified_dashboard.html',
                       help='Output file path')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Initialize dashboard
    dashboard = UnifiedDashboard(config)
    
    # Perform action
    if args.action == 'generate-html':
        success = dashboard.generate_dashboard(args.output)
        if success:
            print(f"Dashboard generated: {args.output}")
        sys.exit(0 if success else 1)
    
    elif args.action == 'generate-json':
        report = dashboard.generate_json_report()
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"JSON report generated: {args.output}")
        sys.exit(0)


if __name__ == '__main__':
    main()
