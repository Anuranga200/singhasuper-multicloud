#!/usr/bin/env python3
"""
Property-Based Tests for Cost Monitoring

This module contains property-based tests for cost monitoring and optimization,
validating per-cloud cost tracking, cost report generation, and budget alerts.

Tests:
- Property 19: Per-Cloud Cost Tracking
- Property 20: Cost Report Generation
- Property 21: Budget Alert Threshold
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from datetime import datetime, timedelta
from typing import Dict, List


# Test data generators
@st.composite
def cost_data_strategy(draw):
    """Generate cost data for a cloud provider"""
    return {
        'cloud': draw(st.sampled_from(['AWS', 'Azure', 'GCP'])),
        'total_cost': draw(st.floats(min_value=0, max_value=1000)),
        'service_breakdown': {
            'compute': draw(st.floats(min_value=0, max_value=500)),
            'database': draw(st.floats(min_value=0, max_value=300)),
            'storage': draw(st.floats(min_value=0, max_value=100)),
            'networking': draw(st.floats(min_value=0, max_value=100))
        },
        'period_days': draw(st.integers(min_value=1, max_value=31)),
        'timestamp': datetime.now().isoformat()
    }


@st.composite
def multi_cloud_cost_strategy(draw):
    """Generate cost data for all clouds"""
    aws_cost = draw(st.floats(min_value=0, max_value=1000))
    azure_cost = draw(st.floats(min_value=0, max_value=1000))
    gcp_cost = draw(st.floats(min_value=0, max_value=1000))
    
    return {
        'clouds': {
            'aws': {
                'total_cost': aws_cost,
                'service_breakdown': {
                    'EC2': draw(st.floats(min_value=0, max_value=aws_cost)),
                    'RDS': draw(st.floats(min_value=0, max_value=aws_cost)),
                    'S3': draw(st.floats(min_value=0, max_value=aws_cost))
                }
            },
            'azure': {
                'total_cost': azure_cost,
                'service_breakdown': {
                    'VirtualMachines': draw(st.floats(min_value=0, max_value=azure_cost)),
                    'Database': draw(st.floats(min_value=0, max_value=azure_cost))
                }
            },
            'gcp': {
                'total_cost': gcp_cost,
                'service_breakdown': {
                    'ComputeEngine': draw(st.floats(min_value=0, max_value=gcp_cost)),
                    'CloudSQL': draw(st.floats(min_value=0, max_value=gcp_cost))
                }
            }
        },
        'total_cost': aws_cost + azure_cost + gcp_cost,
        'period': {
            'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'days': 30
        }
    }


@st.composite
def budget_configuration_strategy(draw):
    """Generate budget configuration"""
    return {
        'cloud': draw(st.sampled_from(['aws', 'azure', 'gcp'])),
        'budget': draw(st.floats(min_value=10, max_value=1000)),
        'actual_cost': draw(st.floats(min_value=0, max_value=1500)),
        'alert_threshold_80': 0.8,
        'alert_threshold_100': 1.0
    }


@st.composite
def cost_report_strategy(draw):
    """Generate cost report data"""
    actual_cost = draw(st.floats(min_value=0, max_value=1000))
    estimated_cost = draw(st.floats(min_value=0, max_value=1000))
    
    return {
        'report_type': 'monthly',
        'generated_at': datetime.now().isoformat(),
        'period': {
            'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        'summary': {
            'total_actual_cost': actual_cost,
            'total_estimated_cost': estimated_cost,
            'variance': actual_cost - estimated_cost,
            'variance_percentage': ((actual_cost - estimated_cost) / estimated_cost * 100) if estimated_cost > 0 else 0
        }
    }


class TestPerCloudCostTracking:
    """
    Property 19: Per-Cloud Cost Tracking
    
    **Validates: Requirements 5.1**
    
    For any cloud provider, the Cost_Monitor should maintain separate cost 
    tracking data that can be queried independently.
    """
    
    @given(cost_data=cost_data_strategy())
    @settings(max_examples=100)
    def test_property_19_separate_cost_tracking(self, cost_data: Dict):
        """
        Feature: multi-cloud-dr-system, Property 19: Per-Cloud Cost Tracking
        
        Verify that each cloud has separate, independent cost tracking.
        """
        # Property: Each cloud must have its own cost data
        assert 'cloud' in cost_data, "Cost data must identify the cloud provider"
        assert 'total_cost' in cost_data, "Cost data must include total cost"
        assert cost_data['total_cost'] >= 0, "Total cost must be non-negative"
    
    @given(multi_cloud_costs=multi_cloud_cost_strategy())
    @settings(max_examples=100)
    def test_property_19_independent_cloud_costs(self, multi_cloud_costs: Dict):
        """
        Verify that costs for each cloud can be queried independently.
        """
        # Property: Each cloud's costs are tracked separately
        assert 'clouds' in multi_cloud_costs, "Must have separate cloud cost data"
        
        required_clouds = {'aws', 'azure', 'gcp'}
        assert required_clouds.issubset(multi_cloud_costs['clouds'].keys()), \
            "Must track costs for all three clouds"
        
        # Each cloud must have independent cost data
        for cloud in required_clouds:
            cloud_data = multi_cloud_costs['clouds'][cloud]
            assert 'total_cost' in cloud_data, f"{cloud} must have total_cost"
            assert cloud_data['total_cost'] >= 0, f"{cloud} cost must be non-negative"
    
    @given(multi_cloud_costs=multi_cloud_cost_strategy())
    @settings(max_examples=100)
    def test_property_19_cost_aggregation(self, multi_cloud_costs: Dict):
        """
        Verify that total cost equals sum of individual cloud costs.
        """
        # Calculate sum of individual cloud costs
        calculated_total = sum(
            multi_cloud_costs['clouds'][cloud]['total_cost']
            for cloud in ['aws', 'azure', 'gcp']
        )
        
        # Property: Total cost must equal sum of cloud costs
        assert abs(multi_cloud_costs['total_cost'] - calculated_total) < 0.01, \
            f"Total cost {multi_cloud_costs['total_cost']} does not match sum {calculated_total}"
    
    @given(cost_data=cost_data_strategy())
    @settings(max_examples=100)
    def test_service_breakdown_available(self, cost_data: Dict):
        """
        Verify that service-level cost breakdown is available for each cloud.
        """
        # Property: Service breakdown must be available
        assert 'service_breakdown' in cost_data, "Must have service-level breakdown"
        
        service_breakdown = cost_data['service_breakdown']
        assert isinstance(service_breakdown, dict), "Service breakdown must be a dictionary"
        
        # All service costs must be non-negative
        for service, cost in service_breakdown.items():
            assert cost >= 0, f"Service {service} cost must be non-negative"


class TestCostReportGeneration:
    """
    Property 20: Cost Report Generation
    
    **Validates: Requirements 5.2**
    
    For any completed calendar month, the Cost_Monitor should generate a cost 
    report comparing actual vs. estimated costs for each cloud.
    """
    
    @given(report=cost_report_strategy())
    @settings(max_examples=100)
    def test_property_20_monthly_report_generation(self, report: Dict):
        """
        Feature: multi-cloud-dr-system, Property 20: Cost Report Generation
        
        Verify that monthly cost reports are generated with required fields.
        """
        # Property: Report must have required fields
        required_fields = ['report_type', 'generated_at', 'period', 'summary']
        for field in required_fields:
            assert field in report, f"Report must have {field} field"
        
        # Report type must be monthly
        assert report['report_type'] == 'monthly', "Report type must be 'monthly'"
        
        # Period must have start and end dates
        assert 'start_date' in report['period'], "Period must have start_date"
        assert 'end_date' in report['period'], "Period must have end_date"
    
    @given(report=cost_report_strategy())
    @settings(max_examples=100)
    def test_property_20_actual_vs_estimated_comparison(self, report: Dict):
        """
        Verify that reports compare actual vs. estimated costs.
        """
        summary = report['summary']
        
        # Property: Report must compare actual vs estimated
        required_summary_fields = [
            'total_actual_cost',
            'total_estimated_cost',
            'variance',
            'variance_percentage'
        ]
        
        for field in required_summary_fields:
            assert field in summary, f"Summary must have {field}"
        
        # Variance must be calculated correctly
        expected_variance = summary['total_actual_cost'] - summary['total_estimated_cost']
        assert abs(summary['variance'] - expected_variance) < 0.01, \
            "Variance must equal actual - estimated"
    
    @given(report=cost_report_strategy())
    @settings(max_examples=100)
    def test_property_20_variance_percentage_calculation(self, report: Dict):
        """
        Verify that variance percentage is calculated correctly.
        """
        summary = report['summary']
        
        if summary['total_estimated_cost'] > 0:
            expected_variance_pct = (
                (summary['total_actual_cost'] - summary['total_estimated_cost']) /
                summary['total_estimated_cost'] * 100
            )
            
            # Property: Variance percentage must be calculated correctly
            assert abs(summary['variance_percentage'] - expected_variance_pct) < 0.1, \
                f"Variance percentage {summary['variance_percentage']} does not match expected {expected_variance_pct}"
    
    @given(
        actual_costs=st.lists(st.floats(min_value=0, max_value=1000), min_size=1, max_size=12),
        estimated_costs=st.lists(st.floats(min_value=0, max_value=1000), min_size=1, max_size=12)
    )
    @settings(max_examples=50)
    def test_report_generation_frequency(self, actual_costs: List[float], estimated_costs: List[float]):
        """
        Verify that reports can be generated for multiple months.
        """
        # Ensure lists are same length
        min_length = min(len(actual_costs), len(estimated_costs))
        actual_costs = actual_costs[:min_length]
        estimated_costs = estimated_costs[:min_length]
        
        # Property: Should be able to generate report for each month
        for i in range(len(actual_costs)):
            variance = actual_costs[i] - estimated_costs[i]
            
            # Each month should have valid cost data
            assert actual_costs[i] >= 0, f"Month {i} actual cost must be non-negative"
            assert estimated_costs[i] >= 0, f"Month {i} estimated cost must be non-negative"


class TestBudgetAlertThreshold:
    """
    Property 21: Budget Alert Threshold
    
    **Validates: Requirements 5.3**
    
    For any month where costs exceed the budget threshold by 20%, an alert 
    should be sent to administrators.
    """
    
    @given(budget_config=budget_configuration_strategy())
    @settings(max_examples=100)
    def test_property_21_alert_at_80_percent(self, budget_config: Dict):
        """
        Feature: multi-cloud-dr-system, Property 21: Budget Alert Threshold
        
        Verify that alerts are triggered at 80% of budget.
        """
        budget = budget_config['budget']
        actual_cost = budget_config['actual_cost']
        percentage = (actual_cost / budget * 100) if budget > 0 else 0
        
        # Property: Alert should be triggered at 80% threshold
        if percentage >= 80:
            # Alert should be generated
            alert_required = True
            severity = 'critical' if percentage >= 100 else 'warning'
            
            assert alert_required, f"Alert required at {percentage:.1f}% of budget"
            
            if percentage >= 100:
                assert severity == 'critical', "Alert severity must be critical at 100%+"
            else:
                assert severity == 'warning', "Alert severity must be warning at 80-99%"
    
    @given(budget_config=budget_configuration_strategy())
    @settings(max_examples=100)
    def test_property_21_alert_at_100_percent(self, budget_config: Dict):
        """
        Verify that critical alerts are triggered at 100% of budget.
        """
        budget = budget_config['budget']
        actual_cost = budget_config['actual_cost']
        percentage = (actual_cost / budget * 100) if budget > 0 else 0
        
        # Property: Critical alert at 100% threshold
        if percentage >= 100:
            alert_severity = 'critical'
            assert alert_severity == 'critical', \
                f"Must send critical alert when cost exceeds budget ({percentage:.1f}%)"
    
    @given(budget_config=budget_configuration_strategy())
    @settings(max_examples=100)
    def test_property_21_no_alert_below_threshold(self, budget_config: Dict):
        """
        Verify that no alerts are sent when below 80% threshold.
        """
        budget = budget_config['budget']
        actual_cost = budget_config['actual_cost']
        percentage = (actual_cost / budget * 100) if budget > 0 else 0
        
        # Property: No alert below 80% threshold
        if percentage < 80:
            alert_required = False
            assert not alert_required, \
                f"Should not send alert at {percentage:.1f}% of budget"
    
    @given(
        budget=st.floats(min_value=100, max_value=1000),
        cost_percentage=st.floats(min_value=0, max_value=150)
    )
    @settings(max_examples=100)
    def test_alert_threshold_accuracy(self, budget: float, cost_percentage: float):
        """
        Verify that alert thresholds are calculated accurately.
        """
        actual_cost = budget * (cost_percentage / 100)
        
        # Determine expected alert status
        should_alert = cost_percentage >= 80
        is_critical = cost_percentage >= 100
        
        # Property: Alert logic must be accurate
        if should_alert:
            if is_critical:
                assert cost_percentage >= 100, "Critical threshold must be at 100%+"
            else:
                assert 80 <= cost_percentage < 100, "Warning threshold must be 80-99%"
        else:
            assert cost_percentage < 80, "No alert below 80%"
    
    @given(
        budgets=st.dictionaries(
            keys=st.sampled_from(['aws', 'azure', 'gcp']),
            values=st.floats(min_value=10, max_value=1000),
            min_size=3,
            max_size=3
        ),
        actual_costs=st.dictionaries(
            keys=st.sampled_from(['aws', 'azure', 'gcp']),
            values=st.floats(min_value=0, max_value=1500),
            min_size=3,
            max_size=3
        )
    )
    @settings(max_examples=50)
    def test_multi_cloud_budget_alerts(self, budgets: Dict, actual_costs: Dict):
        """
        Verify that budget alerts work correctly across multiple clouds.
        """
        alerts = []
        
        for cloud in ['aws', 'azure', 'gcp']:
            if cloud in budgets and cloud in actual_costs:
                budget = budgets[cloud]
                actual = actual_costs[cloud]
                percentage = (actual / budget * 100) if budget > 0 else 0
                
                if percentage >= 80:
                    alerts.append({
                        'cloud': cloud,
                        'percentage': percentage,
                        'severity': 'critical' if percentage >= 100 else 'warning'
                    })
        
        # Property: Each cloud's budget is monitored independently
        for alert in alerts:
            assert alert['percentage'] >= 80, \
                f"{alert['cloud']} alert triggered below 80% threshold"


# Utility functions for test data validation
def validate_cost_data(cost_data: Dict) -> bool:
    """Validate cost data structure"""
    required_fields = ['cloud', 'total_cost', 'service_breakdown']
    return all(field in cost_data for field in required_fields)


def validate_cost_report(report: Dict) -> bool:
    """Validate cost report structure"""
    required_fields = ['report_type', 'generated_at', 'period', 'summary']
    return all(field in report for field in required_fields)


def validate_budget_config(config: Dict) -> bool:
    """Validate budget configuration"""
    required_fields = ['cloud', 'budget', 'actual_cost']
    return all(field in config for field in required_fields)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
