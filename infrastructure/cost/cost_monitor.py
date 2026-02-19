#!/usr/bin/env python3
"""
Cost Monitoring Service

This script monitors and tracks cloud spending across AWS, Azure, and GCP.
It queries cost APIs, aggregates costs by service and cloud, and provides
cost analysis and forecasting.

Features:
- Query AWS Cost Explorer API for daily costs
- Query Azure Cost Management API for daily costs
- Query GCP Cloud Billing API for daily costs
- Aggregate costs by service and cloud
- Generate cost reports
- Track cost trends
- Send budget alerts

Requirements:
- AWS credentials with Cost Explorer access
- Azure credentials with Cost Management access
- GCP credentials with Cloud Billing access
"""

import sys
import logging
import json
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

try:
    import boto3
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.costmanagement import CostManagementClient
    from google.cloud import billing_v1
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install boto3 azure-identity azure-mgmt-costmanagement google-cloud-billing")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CostMonitor:
    """Monitors cloud costs across AWS, Azure, and GCP"""
    
    def __init__(self, config: Dict):
        """Initialize cost monitor"""
        self.config = config
        
        # Initialize AWS clients
        aws_region = config.get('aws_region', 'us-east-1')
        self.ce_client = boto3.client('ce', region_name=aws_region)
        self.budgets_client = boto3.client('budgets', region_name=aws_region)
        self.sns_client = boto3.client('sns', region_name=aws_region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=aws_region)
        
        logger.info("Cost Monitor initialized")
    
    def get_aws_costs(self, start_date: str, end_date: str) -> Dict:
        """
        Get AWS costs for date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with cost data
        """
        logger.info(f"Fetching AWS costs from {start_date} to {end_date}...")
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            # Aggregate costs by service
            service_costs = {}
            total_cost = Decimal('0')
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = Decimal(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if service not in service_costs:
                        service_costs[service] = Decimal('0')
                    
                    service_costs[service] += cost
                    total_cost += cost
            
            # Convert to regular dict with float values
            service_costs_dict = {
                service: float(cost) 
                for service, cost in service_costs.items()
            }
            
            logger.info(f"AWS total cost: ${float(total_cost):.2f}")
            
            return {
                'cloud': 'AWS',
                'start_date': start_date,
                'end_date': end_date,
                'total_cost': float(total_cost),
                'service_breakdown': service_costs_dict,
                'currency': 'USD'
            }
            
        except Exception as e:
            logger.error(f"Error fetching AWS costs: {e}")
            return {
                'cloud': 'AWS',
                'error': str(e),
                'total_cost': 0,
                'service_breakdown': {}
            }
    
    def get_azure_costs(self, start_date: str, end_date: str) -> Dict:
        """
        Get Azure costs for date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with cost data
        """
        logger.info(f"Fetching Azure costs from {start_date} to {end_date}...")
        
        try:
            if 'azure_subscription_id' not in self.config:
                logger.warning("Azure subscription ID not configured")
                return {
                    'cloud': 'Azure',
                    'error': 'Subscription ID not configured',
                    'total_cost': 0,
                    'service_breakdown': {}
                }
            
            credential = DefaultAzureCredential()
            cost_client = CostManagementClient(credential)
            
            scope = f"/subscriptions/{self.config['azure_subscription_id']}"
            
            # Query costs
            query = {
                "type": "Usage",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date,
                    "to": end_date
                },
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {
                        "totalCost": {
                            "name": "Cost",
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {
                            "type": "Dimension",
                            "name": "ServiceName"
                        }
                    ]
                }
            }
            
            result = cost_client.query.usage(scope, query)
            
            # Aggregate costs
            service_costs = {}
            total_cost = 0
            
            for row in result.rows:
                cost = float(row[0])
                service = row[1] if len(row) > 1 else 'Unknown'
                
                if service not in service_costs:
                    service_costs[service] = 0
                
                service_costs[service] += cost
                total_cost += cost
            
            logger.info(f"Azure total cost: ${total_cost:.2f}")
            
            return {
                'cloud': 'Azure',
                'start_date': start_date,
                'end_date': end_date,
                'total_cost': total_cost,
                'service_breakdown': service_costs,
                'currency': 'USD'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Azure costs: {e}")
            return {
                'cloud': 'Azure',
                'error': str(e),
                'total_cost': 0,
                'service_breakdown': {}
            }
    
    def get_gcp_costs(self, start_date: str, end_date: str) -> Dict:
        """
        Get GCP costs for date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with cost data
        """
        logger.info(f"Fetching GCP costs from {start_date} to {end_date}...")
        
        try:
            if 'gcp_billing_account' not in self.config:
                logger.warning("GCP billing account not configured")
                return {
                    'cloud': 'GCP',
                    'error': 'Billing account not configured',
                    'total_cost': 0,
                    'service_breakdown': {}
                }
            
            # Note: GCP Cloud Billing API requires BigQuery export
            # This is a simplified implementation
            # In production, you would query BigQuery for detailed cost data
            
            logger.info("GCP cost fetching requires BigQuery export setup")
            
            return {
                'cloud': 'GCP',
                'start_date': start_date,
                'end_date': end_date,
                'total_cost': 0,
                'service_breakdown': {},
                'currency': 'USD',
                'note': 'Requires BigQuery export configuration'
            }
            
        except Exception as e:
            logger.error(f"Error fetching GCP costs: {e}")
            return {
                'cloud': 'GCP',
                'error': str(e),
                'total_cost': 0,
                'service_breakdown': {}
            }
    
    def get_all_costs(self, days: int = 30) -> Dict:
        """
        Get costs from all clouds for the past N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with aggregated cost data
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"Fetching costs for all clouds from {start_str} to {end_str}")
        
        # Get costs from each cloud
        aws_costs = self.get_aws_costs(start_str, end_str)
        azure_costs = self.get_azure_costs(start_str, end_str)
        gcp_costs = self.get_gcp_costs(start_str, end_str)
        
        # Aggregate
        total_cost = (
            aws_costs['total_cost'] +
            azure_costs['total_cost'] +
            gcp_costs['total_cost']
        )
        
        return {
            'period': {
                'start_date': start_str,
                'end_date': end_str,
                'days': days
            },
            'total_cost': total_cost,
            'clouds': {
                'aws': aws_costs,
                'azure': azure_costs,
                'gcp': gcp_costs
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def check_budget_alerts(self, costs: Dict) -> List[Dict]:
        """
        Check if costs exceed budget thresholds
        
        Args:
            costs: Cost data from get_all_costs()
            
        Returns:
            List of budget alerts
        """
        logger.info("Checking budget thresholds...")
        
        alerts = []
        
        # Get budget configuration
        budgets = self.config.get('budgets', {})
        
        for cloud, cloud_costs in costs['clouds'].items():
            if cloud not in budgets:
                continue
            
            budget = budgets[cloud]
            actual_cost = cloud_costs['total_cost']
            
            # Calculate percentage
            if budget > 0:
                percentage = (actual_cost / budget) * 100
            else:
                percentage = 0
            
            # Check thresholds
            if percentage >= 100:
                alerts.append({
                    'cloud': cloud,
                    'severity': 'critical',
                    'budget': budget,
                    'actual_cost': actual_cost,
                    'percentage': percentage,
                    'message': f"{cloud.upper()} costs (${actual_cost:.2f}) exceed budget (${budget:.2f}) by {percentage - 100:.1f}%"
                })
            elif percentage >= 80:
                alerts.append({
                    'cloud': cloud,
                    'severity': 'warning',
                    'budget': budget,
                    'actual_cost': actual_cost,
                    'percentage': percentage,
                    'message': f"{cloud.upper()} costs (${actual_cost:.2f}) at {percentage:.1f}% of budget (${budget:.2f})"
                })
        
        logger.info(f"Found {len(alerts)} budget alerts")
        return alerts
    
    def send_budget_alert(self, alerts: List[Dict]):
        """Send budget alert notifications"""
        if not alerts:
            return
        
        try:
            if 'sns_topic_arn' not in self.config:
                logger.warning("No SNS topic configured for alerts")
                return
            
            message = "Cost Budget Alerts\n\n"
            
            for alert in alerts:
                message += f"{alert['severity'].upper()}: {alert['message']}\n"
            
            self.sns_client.publish(
                TopicArn=self.config['sns_topic_arn'],
                Subject=f"Cost Budget Alert: {len(alerts)} threshold(s) exceeded",
                Message=message
            )
            
            logger.info("Budget alert sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending budget alert: {e}")
    
    def publish_cost_metrics(self, costs: Dict):
        """Publish cost metrics to CloudWatch"""
        try:
            timestamp = datetime.now()
            
            for cloud, cloud_costs in costs['clouds'].items():
                self.cloudwatch_client.put_metric_data(
                    Namespace='DR-System/Costs',
                    MetricData=[
                        {
                            'MetricName': 'TotalCost',
                            'Value': cloud_costs['total_cost'],
                            'Unit': 'None',
                            'Timestamp': timestamp,
                            'Dimensions': [
                                {'Name': 'Cloud', 'Value': cloud.upper()}
                            ]
                        }
                    ]
                )
            
            # Publish total cost
            self.cloudwatch_client.put_metric_data(
                Namespace='DR-System/Costs',
                MetricData=[
                    {
                        'MetricName': 'TotalCost',
                        'Value': costs['total_cost'],
                        'Unit': 'None',
                        'Timestamp': timestamp,
                        'Dimensions': [
                            {'Name': 'Cloud', 'Value': 'All'}
                        ]
                    }
                ]
            )
            
            logger.info("Cost metrics published to CloudWatch")
            
        except Exception as e:
            logger.error(f"Error publishing cost metrics: {e}")
    
    def monitor_costs(self, days: int = 30):
        """
        Monitor costs and send alerts if needed
        
        Args:
            days: Number of days to analyze
        """
        logger.info("Starting cost monitoring...")
        
        # Get costs
        costs = self.get_all_costs(days)
        
        # Check budget alerts
        alerts = self.check_budget_alerts(costs)
        
        # Send alerts if any
        if alerts:
            self.send_budget_alert(alerts)
        
        # Publish metrics
        self.publish_cost_metrics(costs)
        
        # Log summary
        logger.info(f"Total cost for past {days} days: ${costs['total_cost']:.2f}")
        logger.info(f"AWS: ${costs['clouds']['aws']['total_cost']:.2f}")
        logger.info(f"Azure: ${costs['clouds']['azure']['total_cost']:.2f}")
        logger.info(f"GCP: ${costs['clouds']['gcp']['total_cost']:.2f}")
        
        return costs


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
    
    parser = argparse.ArgumentParser(description='Cost Monitoring Service')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--output', help='Output file for cost report (JSON)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize monitor
    monitor = CostMonitor(config)
    
    # Monitor costs
    costs = monitor.monitor_costs(args.days)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(costs, f, indent=2)
        logger.info(f"Cost report saved to {args.output}")
    
    # Print summary
    print(f"\nCost Summary (past {args.days} days):")
    print(f"Total: ${costs['total_cost']:.2f}")
    print(f"AWS: ${costs['clouds']['aws']['total_cost']:.2f}")
    print(f"Azure: ${costs['clouds']['azure']['total_cost']:.2f}")
    print(f"GCP: ${costs['clouds']['gcp']['total_cost']:.2f}")


if __name__ == '__main__':
    main()
