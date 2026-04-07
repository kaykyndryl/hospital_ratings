"""
Impact Estimator Module

Estimates the impact of recommended actions based on historical peer performance.
Uses peer hospital improvement patterns to generate realistic impact estimates.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def benchmark_improvement_rates(hospital_data: pd.DataFrame, metric: str,
                                min_improvement_threshold: float = 0.05) -> Dict:
    """
    Calculate historical improvement rates for a metric based on peer data.

    Args:
        hospital_data: Time-series DataFrame
        metric: Metric to analyze (e.g., 'clabsi_rate')
        min_improvement_threshold: Minimum % improvement to count as "improved"

    Returns:
        Dictionary with improvement statistics
    """
    # Get latest and earliest years
    latest_year = hospital_data['year'].max()
    earliest_year = hospital_data['year'].min()

    # Get latest and earliest data for each hospital
    latest_data = hospital_data[hospital_data['year'] == latest_year]
    earliest_data = hospital_data[hospital_data['year'] == earliest_year]

    if metric not in latest_data.columns or metric not in earliest_data.columns:
        return {
            'metric': metric,
            'hospitals_analyzed': 0,
            'improvement_rate': 0,
            'average_improvement_pct': 0,
            'improvement_range': (0, 0),
            'confidence': 'low'
        }

    # Match hospitals between earliest and latest
    matched_hospitals = []
    for hosp_id in latest_data['hospital_id'].unique():
        earliest = earliest_data[earliest_data['hospital_id'] == hosp_id]
        latest = latest_data[latest_data['hospital_id'] == hosp_id]

        if len(earliest) > 0 and len(latest) > 0:
            earliest_val = float(earliest[metric].iloc[0])
            latest_val = float(latest[metric].iloc[0])

            if earliest_val > 0 and not np.isnan(earliest_val) and not np.isnan(latest_val):
                matched_hospitals.append({
                    'hospital_id': hosp_id,
                    'earliest_value': earliest_val,
                    'latest_value': latest_val,
                    'improvement_pct': ((earliest_val - latest_val) / earliest_val) * 100
                })

    if not matched_hospitals:
        return {
            'metric': metric,
            'hospitals_analyzed': 0,
            'hospitals_improved': 0,
            'improvement_rate': 0,
            'average_improvement_pct': 0,
            'median_improvement_pct': 0,
            'std_dev_improvement': 0,
            'improvement_range': (0, 0),
            'confidence': 'low'
        }

    # Analyze improvements
    improvements = [h for h in matched_hospitals if h['improvement_pct'] > min_improvement_threshold]
    improvement_pcts = [h['improvement_pct'] for h in improvements]

    improvement_rate = len(improvements) / len(matched_hospitals) if matched_hospitals else 0

    return {
        'metric': metric,
        'hospitals_analyzed': len(matched_hospitals),
        'hospitals_improved': len(improvements),
        'improvement_rate': improvement_rate,
        'average_improvement_pct': np.mean(improvement_pcts) if improvement_pcts else 0,
        'median_improvement_pct': np.median(improvement_pcts) if improvement_pcts else 0,
        'std_dev_improvement': np.std(improvement_pcts) if improvement_pcts else 0,
        'improvement_range': (min(improvement_pcts), max(improvement_pcts)) if improvement_pcts else (0, 0),
        'confidence': 'high' if len(improvements) >= 10 else 'medium' if len(improvements) >= 3 else 'low'
    }


def calculate_confidence_interval(improvement_data: Dict) -> Tuple[float, float, str]:
    """
    Calculate 95% confidence interval for improvement estimates.

    Args:
        improvement_data: Dictionary from benchmark_improvement_rates

    Returns:
        Tuple of (lower_bound, upper_bound, confidence_level)
    """
    avg_improvement = improvement_data.get('average_improvement_pct', 0)
    std_dev = improvement_data.get('std_dev_improvement', 0)
    n = improvement_data.get('hospitals_improved', 0)

    if n < 2 or std_dev == 0:
        return (max(0, avg_improvement * 0.5), avg_improvement * 1.5, 'low')

    # Simple 95% CI
    margin_of_error = 1.96 * (std_dev / np.sqrt(n))
    lower = max(0, avg_improvement - margin_of_error)
    upper = avg_improvement + margin_of_error

    confidence = improvement_data.get('confidence', 'low')

    return (lower, upper, confidence)


def estimate_action_impact(recommendation: Dict, hospital: pd.Series,
                          hospital_data: pd.DataFrame) -> Dict:
    """
    Estimate the impact of a recommended action based on peer data.

    Args:
        recommendation: Recommendation dictionary with 'metric' and 'action' keys
        hospital: Hospital data row
        hospital_data: Complete time-series DataFrame

    Returns:
        Impact estimate dictionary
    """
    metric = recommendation.get('metric', '')
    action = recommendation.get('action', '')
    priority = recommendation.get('priority', 'Medium')

    # Map common actions to expected improvement ranges
    action_improvement_multipliers = {
        'CLABSI': {
            'Implement CLABSI protocol': 1.2,
            'Enhance infection prevention': 1.15,
            'Improve catheter management': 1.1,
            'Strengthen hand hygiene': 1.05
        },
        'Readmission': {
            'Improve discharge planning': 1.3,
            'Enhance care coordination': 1.25,
            'Increase follow-up contacts': 1.2,
            'Better medication reconciliation': 1.15
        },
        'Mortality': {
            'Update clinical pathways': 1.25,
            'Improve staff training': 1.2,
            'Enhance monitoring': 1.15,
            'Better resource allocation': 1.1
        },
        'Safety': {
            'Strengthen safety culture': 1.2,
            'Improve incident reporting': 1.15,
            'Enhanced training programs': 1.1,
            'Better protocols': 1.05
        }
    }

    # Determine metric category
    metric_category = None
    if 'clabsi' in metric.lower():
        metric_category = 'CLABSI'
    elif 'readmission' in metric.lower():
        metric_category = 'Readmission'
    elif 'mortality' in metric.lower():
        metric_category = 'Mortality'
    elif 'safety' in metric.lower():
        metric_category = 'Safety'

    # Get benchmark improvement data
    benchmark = benchmark_improvement_rates(hospital_data, metric.replace(' ', '_').lower())
    lower_ci, upper_ci, confidence = calculate_confidence_interval(benchmark)

    # Apply action multiplier if known
    base_improvement = benchmark.get('average_improvement_pct', 0) or 5.0  # Default to 5% if no data
    action_multiplier = 1.0

    if metric_category and metric_category in action_improvement_multipliers:
        for action_keyword, multiplier in action_improvement_multipliers[metric_category].items():
            if action_keyword.lower() in action.lower():
                action_multiplier = multiplier
                break

    # Calculate expected impact
    estimated_improvement = base_improvement * action_multiplier
    estimated_lower = lower_ci * action_multiplier
    estimated_upper = upper_ci * action_multiplier

    # Estimate timeframe based on priority
    timeframes = {
        'High': '3-6 months',
        'Medium': '6-12 months',
        'Low': '12-18 months'
    }

    # Current value (for percentage reference)
    current_value = float(hospital.get(metric.replace(' ', '_').lower(), 0))
    if current_value == 0:
        current_value = 1.0  # Avoid division by zero

    return {
        'metric': metric,
        'action': action,
        'priority': priority,
        'current_value': current_value,
        'estimated_improvement_pct': estimated_improvement,
        'estimated_improvement_range': (estimated_lower, estimated_upper),
        'estimated_new_value': current_value * (1 - estimated_improvement / 100) if 'rating' not in metric.lower() else current_value + (current_value * estimated_improvement / 100),
        'confidence_level': confidence,
        'estimated_timeframe': timeframes.get(priority, '6-12 months'),
        'peer_evidence': {
            'hospitals_analyzed': benchmark.get('hospitals_analyzed', 0),
            'hospitals_improved': benchmark.get('hospitals_improved', 0),
            'average_peer_improvement': benchmark.get('average_improvement_pct', 0)
        }
    }


def generate_impact_narrative(impact_estimate: Dict) -> str:
    """
    Convert impact estimate into human-readable narrative.

    Args:
        impact_estimate: Impact estimate dictionary

    Returns:
        Human-readable impact description
    """
    metric = impact_estimate['metric']
    improvement = impact_estimate['estimated_improvement_pct']
    lower, upper = impact_estimate['estimated_improvement_range']
    timeframe = impact_estimate['estimated_timeframe']
    confidence = impact_estimate['confidence_level']
    peer_improved = impact_estimate['peer_evidence']['hospitals_improved']

    confidence_emoji = {'high': '📊', 'medium': '📈', 'low': '⚠️'}[confidence]

    narrative = (
        f"**{metric}**: Est. {improvement:.1f}% improvement "
        f"({lower:.1f}% - {upper:.1f}% range) "
        f"within {timeframe}. "
        f"{confidence_emoji} {confidence.capitalize()} confidence "
        f"({peer_improved} peer hospitals showed similar improvements)."
    )

    return narrative


def prioritize_recommendations_by_impact(recommendations: List[Dict],
                                        hospital: pd.Series,
                                        hospital_data: pd.DataFrame) -> List[Dict]:
    """
    Score and prioritize recommendations based on impact potential.

    Args:
        recommendations: List of recommendation dictionaries
        hospital: Hospital data
        hospital_data: Complete time-series DataFrame

    Returns:
        Sorted list of recommendations with impact scores
    """
    scored_recommendations = []

    for rec in recommendations:
        impact = estimate_action_impact(rec, hospital, hospital_data)
        impact['narrative'] = generate_impact_narrative(impact)

        # Calculate impact score (for ranking)
        improvement_score = impact['estimated_improvement_pct']
        confidence_multiplier = {'high': 1.0, 'medium': 0.8, 'low': 0.6}[impact['confidence_level']]
        priority_multiplier = {'High': 1.5, 'Medium': 1.0, 'Low': 0.5}[impact['priority']]

        impact['impact_score'] = improvement_score * confidence_multiplier * priority_multiplier

        scored_recommendations.append(impact)

    # Sort by impact score
    return sorted(scored_recommendations, key=lambda x: x['impact_score'], reverse=True)
