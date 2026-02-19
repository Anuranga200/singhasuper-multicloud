#!/usr/bin/env python3
"""
GCP Cloud Monitoring Dashboard Configuration

This script creates and manages GCP Cloud Monitoring dashboards for monitoring
GCP infrastructure including Compute Engine, Cloud SQL, and Load Balancer metrics.

Features:
- Compute Engine instance health and metrics
- Cloud SQL metrics and replication lag
- Load Balancer metrics
- Custom metrics and alerts
- Dashboard templates

Requirements:
- GCP credentials with Monitoring permissions
"""

import sys
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    from google.cloud import monitoring_v3
    from google.cloud.monitoring_dashboard import v1
    from google.oauth2 import service_account
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install google-cloud-monitoring google-cloud-monitoring-dashboards")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GCPMonitoringDashboard:
    """Manages GCP Cloud Monitoring dashboards"""
    
    def __init__(self, config: Dict):
        """
        Initialize GCP Monitoring dashboard manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.project_id = config['gcp_project_id']
        
        # Initialize clients
        if 'gcp_credentials_file' in config:
            credentials = service_account.Credentials.from_service_account_file(
                config['gcp_credentials_file']
            )
            self.dashboard_client = v1.DashboardsServiceClient(credentials=credentials)
            self.alert_client = monitoring_v3.AlertPolicyServiceClient(credentials=credentials)
        else:
            self.dashboard_client = v1.DashboardsServiceClient()
            self.alert_client = monitoring_v3.AlertPolicyServiceClient()
        
        self.project_name = f"projects/{self.project_id}"
        
        logger.info(f"GCP Monitoring Dashboard Manager initialized for project {self.project_id}")
    
    def create_dashboard(self, dashboard_name: str = "MultiCloudDR-GCP") -> bool:
        """
        Create GCP Cloud Monitoring dashboard
        
        Args:
            dashboard_name: Name of the dashboard
            
        Returns:
            True if successful
        """
        logger.info(f"Creating GCP Cloud Monitoring dashboard: {dashboard_name}")
        
        try:
            dashboard = self._build_dashboard(dashboard_name)
            
            # Create dashboard
            request = v1.CreateDashboardRequest(
                parent=self.project_name,
                dashboard=dashboard
            )
            
            response = self.dashboard_client.create_dashboard(request=request)
            
            logger.info(f"Dashboard created successfully: {response.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return False
    
    def _build_dashboard(self, dashboard_name: str) -> v1.Dashboard:
        """
        Build dashboard configuration
        
        Args:
            dashboard_name: Dashboard name
            
        Returns:
            Dashboard object
        """
        instance_name = self.config.get('gcp_instance_name', 'singha-loyalty-mysql-gcp')
        
        dashboard = v1.Dashboard(
            display_name=dashboard_name,
            grid_layout=v1.GridLayout(
                widgets=self._create_widgets(instance_name)
            )
        )
        
        return dashboard
    
    def _create_widgets(self, instance_name: str) -> List:
        """Create dashboard widgets"""
        widgets = []
        
        # Widget 1: Compute Engine CPU Utilization
        widgets.append(v1.Widget(
            title="Compute Engine CPU Utilization",
            xy_chart=v1.XyChart(
                data_sets=[v1.XyChart.DataSet(
                    time_series_query=v1.TimeSeriesQuery(
                        time_series_filter=v1.TimeSeriesFilter(
                            filter='metric.type="compute.googleapis.com/instance/cpu/utilization" resource.type="gce_instance"',
                            aggregation=v1.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=v1.Aggregation.Aligner.ALIGN_MEAN
                            )
                        )
                    ),
                    plot_type=v1.XyChart.DataSet.PlotType.LINE
                )],
                y_axis=v1.XyChart.Axis(
                    label="CPU Utilization",
                    scale=v1.XyChart.Axis.Scale.LINEAR
                )
            )
        ))
        
        # Widget 2: Compute Engine Network Traffic
        widgets.append(v1.Widget(
            title="Compute Engine Network Traffic",
            xy_chart=v1.XyChart(
                data_sets=[
                    v1.XyChart.DataSet(
                        time_series_query=v1.TimeSeriesQuery(
                            time_series_filter=v1.TimeSeriesFilter(
                                filter='metric.type="compute.googleapis.com/instance/network/received_bytes_count" resource.type="gce_instance"',
                                aggregation=v1.Aggregation(
                                    alignment_period={"seconds": 60},
                                    per_series_aligner=v1.Aggregation.Aligner.ALIGN_RATE
                                )
                            )
                        ),
                        plot_type=v1.XyChart.DataSet.PlotType.LINE
                    ),
                    v1.XyChart.DataSet(
                        time_series_query=v1.TimeSeriesQuery(
                            time_series_filter=v1.TimeSeriesFilter(
                                filter='metric.type="compute.googleapis.com/instance/network/sent_bytes_count" resource.type="gce_instance"',
                                aggregation=v1.Aggregation(
                                    alignment_period={"seconds": 60},
                                    per_series_aligner=v1.Aggregation.Aligner.ALIGN_RATE
                                )
                            )
                        ),
                        plot_type=v1.XyChart.DataSet.PlotType.LINE
                    )
                ]
            )
        ))
        
        # Widget 3: Cloud SQL CPU Utilization
        widgets.append(v1.Widget(
            title="Cloud SQL CPU Utilization",
            xy_chart=v1.XyChart(
                data_sets=[v1.XyChart.DataSet(
                    time_series_query=v1.TimeSeriesQuery(
                        time_series_filter=v1.TimeSeriesFilter(
                            filter=f'metric.type="cloudsql.googleapis.com/database/cpu/utilization" resource.type="cloudsql_database" resource.label.database_id="{self.project_id}:{instance_name}"',
                            aggregation=v1.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=v1.Aggregation.Aligner.ALIGN_MEAN
                            )
                        )
                    ),
                    plot_type=v1.XyChart.DataSet.PlotType.LINE
                )],
                y_axis=v1.XyChart.Axis(
                    label="CPU Utilization",
                    scale=v1.XyChart.Axis.Scale.LINEAR
                )
            )
        ))
        
        # Widget 4: Cloud SQL Connections
        widgets.append(v1.Widget(
            title="Cloud SQL Active Connections",
            xy_chart=v1.XyChart(
                data_sets=[v1.XyChart.DataSet(
                    time_series_query=v1.TimeSeriesQuery(
                        time_series_filter=v1.TimeSeriesFilter(
                            filter=f'metric.type="cloudsql.googleapis.com/database/mysql/connections" resource.type="cloudsql_database" resource.label.database_id="{self.project_id}:{instance_name}"',
                            aggregation=v1.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=v1.Aggregation.Aligner.ALIGN_MEAN
                            )
                        )
                    ),
                    plot_type=v1.XyChart.DataSet.PlotType.LINE
                )]
            )
        ))
        
        # Widget 5: Cloud SQL Replication Lag
        widgets.append(v1.Widget(
            title="Cloud SQL Replication Lag",
            xy_chart=v1.XyChart(
                data_sets=[v1.XyChart.DataSet(
                    time_series_query=v1.TimeSeriesQuery(
                        time_series_filter=v1.TimeSeriesFilter(
                            filter=f'metric.type="cloudsql.googleapis.com/database/replication/replica_lag" resource.type="cloudsql_database" resource.label.database_id="{self.project_id}:{instance_name}"',
                            aggregation=v1.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=v1.Aggregation.Aligner.ALIGN_MAX
                            )
                        )
                    ),
                    plot_type=v1.XyChart.DataSet.PlotType.LINE,
                    target_axis=v1.XyChart.DataSet.TargetAxis.Y1
                )],
                y_axis=v1.XyChart.Axis(
                    label="Lag (seconds)",
                    scale=v1.XyChart.Axis.Scale.LINEAR
                ),
                thresholds=[v1.Threshold(
                    value=5.0,
                    color=v1.Threshold.Color.RED,
                    direction=v1.Threshold.Direction.ABOVE
                )]
            )
        ))
        
        # Widget 6: Cloud SQL Memory Usage
        widgets.append(v1.Widget(
            title="Cloud SQL Memory Usage",
            xy_chart=v1.XyChart(
                data_sets=[v1.XyChart.DataSet(
                    time_series_query=v1.TimeSeriesQuery(
                        time_series_filter=v1.TimeSeriesFilter(
                            filter=f'metric.type="cloudsql.googleapis.com/database/memory/utilization" resource.type="cloudsql_database" resource.label.database_id="{self.project_id}:{instance_name}"',
                            aggregation=v1.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=v1.Aggregation.Aligner.ALIGN_MEAN
                            )
                        )
                    ),
                    plot_type=v1.XyChart.DataSet.PlotType.LINE
                )]
            )
        ))
        
        # Widget 7: Load Balancer Request Count
        widgets.append(v1.Widget(
            title="Load Balancer Request Count",
            xy_chart=v1.XyChart(
                data_sets=[v1.XyChart.DataSet(
                    time_series_query=v1.TimeSeriesQuery(
                        time_series_filter=v1.TimeSeriesFilter(
                            filter='metric.type="loadbalancing.googleapis.com/https/request_count" resource.type="https_lb_rule"',
                            aggregation=v1.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=v1.Aggregation.Aligner.ALIGN_RATE
                            )
                        )
                    ),
                    plot_type=v1.XyChart.DataSet.PlotType.LINE
                )]
            )
        ))
        
        # Widget 8: Load Balancer Latency
        widgets.append(v1.Widget(
            title="Load Balancer Backend Latency",
            xy_chart=v1.XyChart(
                data_sets=[v1.XyChart.DataSet(
                    time_series_query=v1.TimeSeriesQuery(
                        time_series_filter=v1.TimeSeriesFilter(
                            filter='metric.type="loadbalancing.googleapis.com/https/backend_latencies" resource.type="https_lb_rule"',
                            aggregation=v1.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=v1.Aggregation.Aligner.ALIGN_MEAN
                            )
                        )
                    ),
                    plot_type=v1.XyChart.DataSet.PlotType.LINE
                )],
                y_axis=v1.XyChart.Axis(
                    label="Latency (ms)",
                    scale=v1.XyChart.Axis.Scale.LINEAR
                )
            )
        ))
        
        return widgets
    
    def create_alert_policies(self) -> bool:
        """
        Create alert policies for critical metrics
        
        Returns:
            True if successful
        """
        logger.info("Creating GCP alert policies...")
        
        try:
            instance_name = self.config.get('gcp_instance_name', 'singha-loyalty-mysql-gcp')
            notification_channel = self.config.get('gcp_notification_channel')
            
            policies = [
                {
                    'display_name': 'GCP-ComputeEngine-HighCPU',
                    'conditions': [{
                        'display_name': 'CPU utilization exceeds 80%',
                        'condition_threshold': {
                            'filter': 'metric.type="compute.googleapis.com/instance/cpu/utilization" resource.type="gce_instance"',
                            'comparison': 'COMPARISON_GT',
                            'threshold_value': 0.8,
                            'duration': {'seconds': 300},
                            'aggregations': [{
                                'alignment_period': {'seconds': 60},
                                'per_series_aligner': 'ALIGN_MEAN'
                            }]
                        }
                    }]
                },
                {
                    'display_name': 'GCP-CloudSQL-HighCPU',
                    'conditions': [{
                        'display_name': 'Cloud SQL CPU exceeds 80%',
                        'condition_threshold': {
                            'filter': f'metric.type="cloudsql.googleapis.com/database/cpu/utilization" resource.type="cloudsql_database" resource.label.database_id="{self.project_id}:{instance_name}"',
                            'comparison': 'COMPARISON_GT',
                            'threshold_value': 0.8,
                            'duration': {'seconds': 300},
                            'aggregations': [{
                                'alignment_period': {'seconds': 60},
                                'per_series_aligner': 'ALIGN_MEAN'
                            }]
                        }
                    }]
                },
                {
                    'display_name': 'GCP-CloudSQL-HighReplicationLag',
                    'conditions': [{
                        'display_name': 'Replication lag exceeds 5 seconds',
                        'condition_threshold': {
                            'filter': f'metric.type="cloudsql.googleapis.com/database/replication/replica_lag" resource.type="cloudsql_database" resource.label.database_id="{self.project_id}:{instance_name}"',
                            'comparison': 'COMPARISON_GT',
                            'threshold_value': 5.0,
                            'duration': {'seconds': 180},
                            'aggregations': [{
                                'alignment_period': {'seconds': 60},
                                'per_series_aligner': 'ALIGN_MAX'
                            }]
                        }
                    }]
                }
            ]
            
            for policy_config in policies:
                policy = monitoring_v3.AlertPolicy(
                    display_name=policy_config['display_name'],
                    conditions=[monitoring_v3.AlertPolicy.Condition(**cond) for cond in policy_config['conditions']],
                    combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.OR,
                    enabled=True
                )
                
                if notification_channel:
                    policy.notification_channels = [notification_channel]
                
                request = monitoring_v3.CreateAlertPolicyRequest(
                    name=self.project_name,
                    alert_policy=policy
                )
                
                response = self.alert_client.create_alert_policy(request=request)
                logger.info(f"Created alert policy: {response.name}")
            
            logger.info("All alert policies created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating alert policies: {e}")
            return False
    
    def list_dashboards(self) -> List[str]:
        """
        List existing dashboards
        
        Returns:
            List of dashboard names
        """
        try:
            request = v1.ListDashboardsRequest(parent=self.project_name)
            dashboards = self.dashboard_client.list_dashboards(request=request)
            
            dashboard_names = [d.display_name for d in dashboards]
            logger.info(f"Found {len(dashboard_names)} dashboards")
            
            return dashboard_names
            
        except Exception as e:
            logger.error(f"Error listing dashboards: {e}")
            return []
    
    def delete_dashboard(self, dashboard_name: str) -> bool:
        """
        Delete dashboard by name
        
        Args:
            dashboard_name: Dashboard name
            
        Returns:
            True if successful
        """
        try:
            # List dashboards to find the one to delete
            request = v1.ListDashboardsRequest(parent=self.project_name)
            dashboards = self.dashboard_client.list_dashboards(request=request)
            
            for dashboard in dashboards:
                if dashboard.display_name == dashboard_name:
                    delete_request = v1.DeleteDashboardRequest(name=dashboard.name)
                    self.dashboard_client.delete_dashboard(request=delete_request)
                    logger.info(f"Dashboard deleted: {dashboard_name}")
                    return True
            
            logger.warning(f"Dashboard not found: {dashboard_name}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting dashboard: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GCP Cloud Monitoring Dashboard Manager')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--action', required=True, 
                       choices=['create', 'delete', 'list', 'create-alerts'],
                       help='Action to perform')
    parser.add_argument('--dashboard-name', default='MultiCloudDR-GCP',
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
    manager = GCPMonitoringDashboard(config)
    
    # Perform action
    if args.action == 'create':
        success = manager.create_dashboard(args.dashboard_name)
        if success:
            print(f"Dashboard created: {args.dashboard_name}")
            print(f"View at: https://console.cloud.google.com/monitoring/dashboards?project={config['gcp_project_id']}")
        sys.exit(0 if success else 1)
    
    elif args.action == 'delete':
        success = manager.delete_dashboard(args.dashboard_name)
        sys.exit(0 if success else 1)
    
    elif args.action == 'list':
        dashboards = manager.list_dashboards()
        print("\nExisting Dashboards:")
        for name in dashboards:
            print(f"  - {name}")
        sys.exit(0)
    
    elif args.action == 'create-alerts':
        success = manager.create_alert_policies()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
