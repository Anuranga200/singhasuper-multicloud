#!/usr/bin/env python3
"""
AWS CloudWatch Dashboard Configuration

This script creates and manages CloudWatch dashboards for monitoring
AWS infrastructure including EC2, RDS, and ALB metrics.

Features:
- EC2 instance health and metrics
- RDS metrics and replication lag
- ALB metrics and request counts
- Custom metrics and alarms
- Dashboard templates

Requirements:
- AWS credentials with CloudWatch permissions
"""

import sys
import logging
import json
import boto3
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AWSCloudWatchDashboard:
    """Manages AWS CloudWatch dashboards"""
    
    def __init__(self, config: Dict):
        """
        Initialize CloudWatch dashboard manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        aws_region = config.get('aws_region', 'us-east-1')
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.ec2 = boto3.client('ec2', region_name=aws_region)
        self.rds = boto3.client('rds', region_name=aws_region)
        self.elbv2 = boto3.client('elbv2', region_name=aws_region)
        
        logger.info(f"AWS CloudWatch Dashboard Manager initialized for region {aws_region}")
    
    def create_dashboard(self, dashboard_name: str = "MultiCloudDR-AWS") -> bool:
        """
        Create CloudWatch dashboard for AWS metrics
        
        Args:
            dashboard_name: Name of the dashboard
            
        Returns:
            True if successful
        """
        logger.info(f"Creating CloudWatch dashboard: {dashboard_name}")
        
        try:
            # Build dashboard body
            dashboard_body = self._build_dashboard_body()
            
            # Create or update dashboard
            response = self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            logger.info(f"Dashboard created successfully: {dashboard_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return False
    
    def _build_dashboard_body(self) -> Dict:
        """
        Build dashboard body with widgets
        
        Returns:
            Dashboard body dictionary
        """
        widgets = []
        
        # Add EC2 widgets
        widgets.extend(self._create_ec2_widgets())
        
        # Add RDS widgets
        widgets.extend(self._create_rds_widgets())
        
        # Add ALB widgets
        widgets.extend(self._create_alb_widgets())
        
        # Add custom metrics widgets
        widgets.extend(self._create_custom_widgets())
        
        return {"widgets": widgets}
    
    def _create_ec2_widgets(self) -> List[Dict]:
        """Create EC2 monitoring widgets"""
        widgets = []
        
        # EC2 CPU Utilization
        widgets.append({
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/EC2", "CPUUtilization", {"stat": "Average"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "EC2 CPU Utilization",
                "period": 300,
                "yAxis": {
                    "left": {
                        "min": 0,
                        "max": 100
                    }
                }
            }
        })
        
        # EC2 Network In/Out
        widgets.append({
            "type": "metric",
            "x": 12,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/EC2", "NetworkIn", {"stat": "Sum", "label": "Network In"}],
                    [".", "NetworkOut", {"stat": "Sum", "label": "Network Out"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "EC2 Network Traffic",
                "period": 300,
                "yAxis": {
                    "left": {
                        "label": "Bytes"
                    }
                }
            }
        })
        
        # EC2 Status Checks
        widgets.append({
            "type": "metric",
            "x": 0,
            "y": 6,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/EC2", "StatusCheckFailed", {"stat": "Sum"}],
                    [".", "StatusCheckFailed_Instance", {"stat": "Sum"}],
                    [".", "StatusCheckFailed_System", {"stat": "Sum"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "EC2 Status Checks",
                "period": 300
            }
        })
        
        return widgets
    
    def _create_rds_widgets(self) -> List[Dict]:
        """Create RDS monitoring widgets"""
        widgets = []
        
        db_instance_id = self.config.get('aws_db_instance_id', 'singha-loyalty-db-primary')
        
        # RDS CPU Utilization
        widgets.append({
            "type": "metric",
            "x": 12,
            "y": 6,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/RDS", "CPUUtilization", {"stat": "Average", "dimensions": {"DBInstanceIdentifier": db_instance_id}}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "RDS CPU Utilization",
                "period": 300,
                "yAxis": {
                    "left": {
                        "min": 0,
                        "max": 100
                    }
                }
            }
        })
        
        # RDS Database Connections
        widgets.append({
            "type": "metric",
            "x": 0,
            "y": 12,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/RDS", "DatabaseConnections", {"stat": "Average", "dimensions": {"DBInstanceIdentifier": db_instance_id}}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "RDS Database Connections",
                "period": 300
            }
        })
        
        # RDS Read/Write IOPS
        widgets.append({
            "type": "metric",
            "x": 12,
            "y": 12,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/RDS", "ReadIOPS", {"stat": "Average", "dimensions": {"DBInstanceIdentifier": db_instance_id}, "label": "Read IOPS"}],
                    [".", "WriteIOPS", {"stat": "Average", "dimensions": {"DBInstanceIdentifier": db_instance_id}, "label": "Write IOPS"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "RDS IOPS",
                "period": 300
            }
        })
        
        # RDS Replication Lag
        widgets.append({
            "type": "metric",
            "x": 0,
            "y": 18,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/RDS", "ReplicaLag", {"stat": "Average", "dimensions": {"DBInstanceIdentifier": db_instance_id}}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "RDS Replication Lag",
                "period": 60,
                "yAxis": {
                    "left": {
                        "label": "Seconds"
                    }
                },
                "annotations": {
                    "horizontal": [{
                        "value": 5,
                        "label": "SLA Threshold (5s)",
                        "fill": "above",
                        "color": "#ff0000"
                    }]
                }
            }
        })
        
        # RDS Free Storage Space
        widgets.append({
            "type": "metric",
            "x": 12,
            "y": 18,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/RDS", "FreeStorageSpace", {"stat": "Average", "dimensions": {"DBInstanceIdentifier": db_instance_id}}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "RDS Free Storage Space",
                "period": 300,
                "yAxis": {
                    "left": {
                        "label": "Bytes"
                    }
                }
            }
        })
        
        return widgets
    
    def _create_alb_widgets(self) -> List[Dict]:
        """Create ALB monitoring widgets"""
        widgets = []
        
        # ALB Request Count
        widgets.append({
            "type": "metric",
            "x": 0,
            "y": 24,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "RequestCount", {"stat": "Sum"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "ALB Request Count",
                "period": 300
            }
        })
        
        # ALB Target Response Time
        widgets.append({
            "type": "metric",
            "x": 12,
            "y": 24,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "TargetResponseTime", {"stat": "Average"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "ALB Target Response Time",
                "period": 300,
                "yAxis": {
                    "left": {
                        "label": "Seconds"
                    }
                }
            }
        })
        
        # ALB HTTP Status Codes
        widgets.append({
            "type": "metric",
            "x": 0,
            "y": 30,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", {"stat": "Sum", "label": "2XX"}],
                    [".", "HTTPCode_Target_4XX_Count", {"stat": "Sum", "label": "4XX"}],
                    [".", "HTTPCode_Target_5XX_Count", {"stat": "Sum", "label": "5XX"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "ALB HTTP Status Codes",
                "period": 300
            }
        })
        
        # ALB Healthy/Unhealthy Hosts
        widgets.append({
            "type": "metric",
            "x": 12,
            "y": 30,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "HealthyHostCount", {"stat": "Average", "label": "Healthy"}],
                    [".", "UnHealthyHostCount", {"stat": "Average", "label": "Unhealthy"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": self.config.get('aws_region', 'us-east-1'),
                "title": "ALB Target Health",
                "period": 60
            }
        })
        
        return widgets
    
    def _create_custom_widgets(self) -> List[Dict]:
        """Create custom metrics widgets"""
        widgets = []
        
        # System Health Status (text widget)
        widgets.append({
            "type": "text",
            "x": 0,
            "y": 36,
            "width": 24,
            "height": 2,
            "properties": {
                "markdown": "# AWS Multi-Cloud DR System Dashboard\n\n**Region:** " + self.config.get('aws_region', 'us-east-1') + " | **Status:** Active Primary | **Last Updated:** " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        })
        
        return widgets
    
    def create_alarms(self) -> bool:
        """
        Create CloudWatch alarms for critical metrics
        
        Returns:
            True if successful
        """
        logger.info("Creating CloudWatch alarms...")
        
        try:
            db_instance_id = self.config.get('aws_db_instance_id', 'singha-loyalty-db-primary')
            sns_topic_arn = self.config.get('sns_topic_arn')
            
            alarms = [
                # High CPU on EC2
                {
                    'AlarmName': 'AWS-EC2-HighCPU',
                    'MetricName': 'CPUUtilization',
                    'Namespace': 'AWS/EC2',
                    'Statistic': 'Average',
                    'Period': 300,
                    'EvaluationPeriods': 2,
                    'Threshold': 80.0,
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'AlarmDescription': 'EC2 CPU utilization exceeds 80%'
                },
                # High CPU on RDS
                {
                    'AlarmName': 'AWS-RDS-HighCPU',
                    'MetricName': 'CPUUtilization',
                    'Namespace': 'AWS/RDS',
                    'Statistic': 'Average',
                    'Period': 300,
                    'EvaluationPeriods': 2,
                    'Threshold': 80.0,
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
                    'AlarmDescription': 'RDS CPU utilization exceeds 80%'
                },
                # High Replication Lag
                {
                    'AlarmName': 'AWS-RDS-HighReplicationLag',
                    'MetricName': 'ReplicaLag',
                    'Namespace': 'AWS/RDS',
                    'Statistic': 'Average',
                    'Period': 60,
                    'EvaluationPeriods': 3,
                    'Threshold': 5.0,
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
                    'AlarmDescription': 'RDS replication lag exceeds 5 seconds'
                },
                # Low Free Storage
                {
                    'AlarmName': 'AWS-RDS-LowStorage',
                    'MetricName': 'FreeStorageSpace',
                    'Namespace': 'AWS/RDS',
                    'Statistic': 'Average',
                    'Period': 300,
                    'EvaluationPeriods': 1,
                    'Threshold': 5000000000,  # 5 GB
                    'ComparisonOperator': 'LessThanThreshold',
                    'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
                    'AlarmDescription': 'RDS free storage space below 5 GB'
                },
                # Unhealthy Targets
                {
                    'AlarmName': 'AWS-ALB-UnhealthyTargets',
                    'MetricName': 'UnHealthyHostCount',
                    'Namespace': 'AWS/ApplicationELB',
                    'Statistic': 'Average',
                    'Period': 60,
                    'EvaluationPeriods': 2,
                    'Threshold': 1.0,
                    'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
                    'AlarmDescription': 'ALB has unhealthy targets'
                }
            ]
            
            for alarm in alarms:
                if sns_topic_arn:
                    alarm['AlarmActions'] = [sns_topic_arn]
                
                self.cloudwatch.put_metric_alarm(**alarm)
                logger.info(f"Created alarm: {alarm['AlarmName']}")
            
            logger.info("All alarms created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating alarms: {e}")
            return False
    
    def delete_dashboard(self, dashboard_name: str = "MultiCloudDR-AWS") -> bool:
        """
        Delete CloudWatch dashboard
        
        Args:
            dashboard_name: Name of the dashboard
            
        Returns:
            True if successful
        """
        try:
            self.cloudwatch.delete_dashboards(DashboardNames=[dashboard_name])
            logger.info(f"Dashboard deleted: {dashboard_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting dashboard: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS CloudWatch Dashboard Manager')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--action', required=True, 
                       choices=['create', 'delete', 'create-alarms'],
                       help='Action to perform')
    parser.add_argument('--dashboard-name', default='MultiCloudDR-AWS',
                       help='Dashboard name')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Initialize dashboard manager
    manager = AWSCloudWatchDashboard(config)
    
    # Perform action
    if args.action == 'create':
        success = manager.create_dashboard(args.dashboard_name)
        if success:
            print(f"Dashboard created: {args.dashboard_name}")
            print(f"View at: https://console.aws.amazon.com/cloudwatch/home?region={config.get('aws_region', 'us-east-1')}#dashboards:name={args.dashboard_name}")
        sys.exit(0 if success else 1)
    
    elif args.action == 'delete':
        success = manager.delete_dashboard(args.dashboard_name)
        sys.exit(0 if success else 1)
    
    elif args.action == 'create-alarms':
        success = manager.create_alarms()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
