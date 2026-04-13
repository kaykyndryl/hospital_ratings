"""
Cost estimation and calculation utilities for healthcare quality improvements.
Uses industry-standard benchmarks with state-based cost adjustments.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def load_cost_config() -> Dict:
    """Load cost estimates configuration from JSON file."""
    config_path = Path(__file__).parent.parent / "config" / "cost_estimates.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def get_state_multiplier(state: str) -> float:
    """Get cost multiplier for a specific state (default 1.0 if not found)."""
    config = load_cost_config()
    multipliers = config.get('state_cost_multipliers', {})
    return multipliers.get(state, 1.0)


def calculate_metric_cost(metric: str, state: str) -> Optional[Dict]:
    """
    Calculate state-adjusted cost for a quality metric improvement.

    Args:
        metric: Metric name (e.g., 'CLABSI Rate', 'Readmission Rate')
        state: State code (e.g., 'CA', 'NY')

    Returns:
        Dictionary with adjusted costs and reference information
    """
    config = load_cost_config()
    estimates = config.get('cost_estimates', {})

    if metric not in estimates:
        return None

    base_estimate = estimates[metric].copy()
    multiplier = get_state_multiplier(state)

    # Calculate adjusted costs
    adjusted_implementation = int(base_estimate['implementation_cost'] * multiplier)
    adjusted_annual = int(base_estimate['annual_cost'] * multiplier)

    return {
        'metric': metric,
        'description': base_estimate['description'],
        'implementation_cost': adjusted_implementation,
        'annual_cost': adjusted_annual,
        'cost_breakdown': base_estimate['cost_breakdown'],
        'state_multiplier': multiplier,
        'reference': base_estimate['reference'],
        'source': base_estimate['source'],
        'link': base_estimate['link'],
        'citation': base_estimate['citation']
    }


def calculate_total_costs(recommendations: List[Dict], state: str) -> Dict:
    """
    Calculate total implementation and annual costs for all recommendations.

    Args:
        recommendations: List of recommendation dictionaries with 'metric' field
        state: State code

    Returns:
        Dictionary with total and per-recommendation costs
    """
    total_implementation = 0
    total_annual = 0
    costs_by_metric = []

    for rec in recommendations:
        metric = rec.get('metric', '')
        cost_data = calculate_metric_cost(metric, state)

        if cost_data:
            costs_by_metric.append(cost_data)
            total_implementation += cost_data['implementation_cost']
            total_annual += cost_data['annual_cost']

    # Estimate ROI timeframe (typically 12-24 months for healthcare improvements)
    annual_savings_estimate = max(total_annual * 0.3, 0)  # Conservative 30% cost reduction estimate
    if annual_savings_estimate > 0 and total_implementation > 0:
        roi_months = min(24, max(12, int((total_implementation / annual_savings_estimate) * 12)))
    else:
        roi_months = 18

    return {
        'total_implementation_cost': total_implementation,
        'total_annual_cost': total_annual,
        'costs_by_metric': costs_by_metric,
        'estimated_roi_months': roi_months,
        'state': state,
        'state_multiplier': get_state_multiplier(state)
    }


def get_cost_methodology() -> Dict:
    """Get cost methodology and disclaimers."""
    config = load_cost_config()
    return {
        'methodology': config.get('methodology', {}),
        'default_assumption': config.get('default_assumption', {})
    }
