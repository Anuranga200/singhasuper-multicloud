#!/usr/bin/env python3
"""
Cost Reporting Service

This script generates monthly cost reports comparing actual vs estimated costs,
identifies cost trends and anomalies, and provides cost optimization recommendations.

Features:
- Generate monthly cost reports
- Compare actual vs estimated costs
- Identify cost trends and anomalies
- Provide cost breakdown by service
- Generate visualizations (optional)
- Export reports in multiple formats (JSON, CSV, HTML)

Requirements:
- Cost data from cost_monitor.py
- Historical cost data for trend analysis
"""

import sys
import logging
import json
import csv
from typing import Dict, List
from datetime import datetime, timedelta
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CostReporter:
    """Generates cost reports and analysis"""
    
    def __init__(self, config: Dict):
        """Initialize cost reporter"""
        self.config = config
        self.estimated_costs = config.get('estimated_costs', {
            'aws': 76,
            'azure': 70,
            'gcp': 60
        })
        
        logger.info("Cost Reporter initialized")
    
    def generate_monthly_report(self, cost_data: Dict) -> Dict:
        """
        Generate monthly cost report
        
        Args:
            cost_data: Cost data from cost_monitor
            
        Returns:
            Dictionary with report data
        """
        logger.info("Generating monthly cost report...")
        
        report = {
            'report_type': 'monthly',
            'generated_at': datetime.now().isoformat(),
            'period': cost_data['period'],
            'summary': {},
            'clouds': {},
            'trends': {},
            'recommendations': []
        }
        
        # Calculate summary
        total_actual = cost_data['total_cost']
        total_estimated = sum(self.estimated_costs.values())
        variance = total_actual - total_estimated
        variance_percentage = (variance / total_estimated * 100) if total_estimated > 0 else 0
        
        report['summary'] = {
            'total_actual_cost': total_actual,
            'total_estimated_cost': total_estimated,
            'variance': variance,
            'variance_percentage': variance_percentage,
            'status': 'over_budget' if variance > 0 else 'under_budget'
        }
        
        # Analyze each cloud
        for cloud, cloud_costs in cost_data['clouds'].items():
            actual_cost = cloud_costs['total_cost']
            estimated_cost = self.estimated_costs.get(cloud, 0)
            cloud_variance = actual_cost - estimated_cost
            cloud_variance_pct = (cloud_variance / estimated_cost * 100) if estimated_cost > 0 else 0
            
            report['clouds'][cloud] = {
                'actual_cost': actual_cost,
                'estimated_cost': estimated_cost,
                'variance': cloud_variance,
                'variance_percentage': cloud_variance_pct,
                'service_breakdown': cloud_costs.get('service_breakdown', {}),
                'top_services': self._get_top_services(cloud_costs.get('service_breakdown', {}), 5)
            }
            
            # Add recommendations if over budget
            if cloud_variance > estimated_cost * 0.2:  # More than 20% over
                report['recommendations'].append({
                    'cloud': cloud,
                    'severity': 'high',
                    'message': f"{cloud.upper()} costs are {cloud_variance_pct:.1f}% over estimate",
                    'suggestion': f"Review {cloud.upper()} resource usage and consider right-sizing"
                })
        
        logger.info("Monthly report generated successfully")
        return report
    
    def _get_top_services(self, service_breakdown: Dict, top_n: int = 5) -> List[Dict]:
        """Get top N services by cost"""
        if not service_breakdown:
            return []
        
        # Sort services by cost
        sorted_services = sorted(
            service_breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {'service': service, 'cost': cost}
            for service, cost in sorted_services[:top_n]
        ]
    
    def identify_cost_trends(self, historical_data: List[Dict]) -> Dict:
        """
        Identify cost trends from historical data
        
        Args:
            historical_data: List of historical cost data points
            
        Returns:
            Dictionary with trend analysis
        """
        logger.info("Analyzing cost trends...")
        
        if len(historical_data) < 2:
            return {
                'trend': 'insufficient_data',
                'message': 'Need at least 2 data points for trend analysis'
            }
        
        # Calculate trend for each cloud
        trends = {}
        
        for cloud in ['aws', 'azure', 'gcp']:
            costs = [
                data['clouds'][cloud]['total_cost']
                for data in historical_data
                if cloud in data.get('clouds', {})
            ]
            
            if len(costs) < 2:
                trends[cloud] = {'trend': 'insufficient_data'}
                continue
            
            # Simple trend analysis
            recent_cost = costs[-1]
            previous_cost = costs[-2]
            change = recent_cost - previous_cost
            change_percentage = (change / previous_cost * 100) if previous_cost > 0 else 0
            
            # Determine trend
            if abs(change_percentage) < 5:
                trend = 'stable'
            elif change_percentage > 0:
                trend = 'increasing'
            else:
                trend = 'decreasing'
            
            trends[cloud] = {
                'trend': trend,
                'recent_cost': recent_cost,
                'previous_cost': previous_cost,
                'change': change,
                'change_percentage': change_percentage,
                'average_cost': sum(costs) / len(costs)
            }
        
        return trends
    
    def identify_anomalies(self, cost_data: Dict, historical_data: List[Dict]) -> List[Dict]:
        """
        Identify cost anomalies
        
        Args:
            cost_data: Current cost data
            historical_data: Historical cost data
            
        Returns:
            List of anomalies
        """
        logger.info("Identifying cost anomalies...")
        
        anomalies = []
        
        if len(historical_data) < 3:
            return anomalies
        
        for cloud in ['aws', 'azure', 'gcp']:
            # Get historical costs
            historical_costs = [
                data['clouds'][cloud]['total_cost']
                for data in historical_data
                if cloud in data.get('clouds', {})
            ]
            
            if len(historical_costs) < 3:
                continue
            
            # Calculate average and standard deviation
            avg_cost = sum(historical_costs) / len(historical_costs)
            variance = sum((x - avg_cost) ** 2 for x in historical_costs) / len(historical_costs)
            std_dev = variance ** 0.5
            
            # Check current cost
            current_cost = cost_data['clouds'][cloud]['total_cost']
            
            # Anomaly if more than 2 standard deviations from mean
            if abs(current_cost - avg_cost) > 2 * std_dev:
                anomalies.append({
                    'cloud': cloud,
                    'current_cost': current_cost,
                    'average_cost': avg_cost,
                    'std_dev': std_dev,
                    'deviation': abs(current_cost - avg_cost) / std_dev,
                    'message': f"{cloud.upper()} cost (${current_cost:.2f}) is {abs(current_cost - avg_cost) / std_dev:.1f} standard deviations from average (${avg_cost:.2f})"
                })
        
        logger.info(f"Found {len(anomalies)} cost anomalies")
        return anomalies
    
    def generate_recommendations(self, report: Dict) -> List[Dict]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Check for high variance
        for cloud, cloud_data in report['clouds'].items():
            variance_pct = cloud_data['variance_percentage']
            
            if variance_pct > 20:
                recommendations.append({
                    'cloud': cloud,
                    'priority': 'high',
                    'category': 'budget_overrun',
                    'recommendation': f"Investigate {cloud.upper()} cost overrun of {variance_pct:.1f}%",
                    'actions': [
                        'Review resource utilization',
                        'Identify unused resources',
                        'Consider reserved instances',
                        'Optimize instance sizes'
                    ]
                })
            
            # Check top services
            top_services = cloud_data.get('top_services', [])
            if top_services and top_services[0]['cost'] > cloud_data['actual_cost'] * 0.5:
                recommendations.append({
                    'cloud': cloud,
                    'priority': 'medium',
                    'category': 'service_optimization',
                    'recommendation': f"{top_services[0]['service']} accounts for >50% of {cloud.upper()} costs",
                    'actions': [
                        f"Review {top_services[0]['service']} usage",
                        'Look for optimization opportunities',
                        'Consider alternative services'
                    ]
                })
        
        return recommendations
    
    def export_report_json(self, report: Dict, filename: str):
        """Export report as JSON"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Report exported to {filename}")
    
    def export_report_csv(self, report: Dict, filename: str):
        """Export report as CSV"""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write summary
            writer.writerow(['Cost Report Summary'])
            writer.writerow(['Generated At', report['generated_at']])
            writer.writerow(['Period', f"{report['period']['start_date']} to {report['period']['end_date']}"])
            writer.writerow([])
            
            # Write totals
            writer.writerow(['Total Actual Cost', f"${report['summary']['total_actual_cost']:.2f}"])
            writer.writerow(['Total Estimated Cost', f"${report['summary']['total_estimated_cost']:.2f}"])
            writer.writerow(['Variance', f"${report['summary']['variance']:.2f}"])
            writer.writerow(['Variance %', f"{report['summary']['variance_percentage']:.1f}%"])
            writer.writerow([])
            
            # Write cloud breakdown
            writer.writerow(['Cloud', 'Actual Cost', 'Estimated Cost', 'Variance', 'Variance %'])
            for cloud, data in report['clouds'].items():
                writer.writerow([
                    cloud.upper(),
                    f"${data['actual_cost']:.2f}",
                    f"${data['estimated_cost']:.2f}",
                    f"${data['variance']:.2f}",
                    f"{data['variance_percentage']:.1f}%"
                ])
        
        logger.info(f"Report exported to {filename}")
    
    def export_report_html(self, report: Dict, filename: str):
        """Export report as HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Cost Report - {report['generated_at']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .over-budget {{ color: red; }}
        .under-budget {{ color: green; }}
        .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
    </style>
</head>
<body>
    <h1>Multi-Cloud Cost Report</h1>
    <p><strong>Generated:</strong> {report['generated_at']}</p>
    <p><strong>Period:</strong> {report['period']['start_date']} to {report['period']['end_date']}</p>
    
    <h2>Summary</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Total Actual Cost</td>
            <td>${report['summary']['total_actual_cost']:.2f}</td>
        </tr>
        <tr>
            <td>Total Estimated Cost</td>
            <td>${report['summary']['total_estimated_cost']:.2f}</td>
        </tr>
        <tr class="{report['summary']['status']}">
            <td>Variance</td>
            <td>${report['summary']['variance']:.2f} ({report['summary']['variance_percentage']:.1f}%)</td>
        </tr>
    </table>
    
    <h2>Cloud Breakdown</h2>
    <table>
        <tr>
            <th>Cloud</th>
            <th>Actual Cost</th>
            <th>Estimated Cost</th>
            <th>Variance</th>
            <th>Variance %</th>
        </tr>
"""
        
        for cloud, data in report['clouds'].items():
            status_class = 'over-budget' if data['variance'] > 0 else 'under-budget'
            html += f"""
        <tr>
            <td>{cloud.upper()}</td>
            <td>${data['actual_cost']:.2f}</td>
            <td>${data['estimated_cost']:.2f}</td>
            <td class="{status_class}">${data['variance']:.2f}</td>
            <td class="{status_class}">{data['variance_percentage']:.1f}%</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>Recommendations</h2>
"""
        
        for rec in report.get('recommendations', []):
            html += f"""
    <div class="recommendation">
        <strong>{rec['cloud'].upper()}:</strong> {rec['message']}<br>
        <em>{rec['suggestion']}</em>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html)
        
        logger.info(f"Report exported to {filename}")


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
    
    parser = argparse.ArgumentParser(description='Cost Reporting Service')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--cost-data', required=True, help='Path to cost data JSON file')
    parser.add_argument('--format', choices=['json', 'csv', 'html', 'all'], default='all', help='Report format')
    parser.add_argument('--output-prefix', default='cost_report', help='Output file prefix')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Load cost data
    with open(args.cost_data, 'r') as f:
        cost_data = json.load(f)
    
    # Initialize reporter
    reporter = CostReporter(config)
    
    # Generate report
    report = reporter.generate_monthly_report(cost_data)
    
    # Add recommendations
    report['recommendations'].extend(reporter.generate_recommendations(report))
    
    # Export in requested format(s)
    if args.format in ['json', 'all']:
        reporter.export_report_json(report, f"{args.output_prefix}.json")
    
    if args.format in ['csv', 'all']:
        reporter.export_report_csv(report, f"{args.output_prefix}.csv")
    
    if args.format in ['html', 'all']:
        reporter.export_report_html(report, f"{args.output_prefix}.html")
    
    print(f"\nCost Report Generated:")
    print(f"Total Actual: ${report['summary']['total_actual_cost']:.2f}")
    print(f"Total Estimated: ${report['summary']['total_estimated_cost']:.2f}")
    print(f"Variance: ${report['summary']['variance']:.2f} ({report['summary']['variance_percentage']:.1f}%)")
    print(f"Status: {report['summary']['status']}")


if __name__ == '__main__':
    main()
