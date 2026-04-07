"""
Longitudinal Analysis Module

Analyzes hospital performance trends over time, including trend calculations,
peer comparisons, and future projections.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_trend(values: List[float], years: List[int]) -> Optional[float]:
    """
    Calculate percentage change trend from first to last value.

    Args:
        values: List of metric values
        years: List of corresponding years

    Returns:
        Percentage change, or None if calculation not possible
    """
    if len(values) < 2:
        return None

    first_value = values[0]
    last_value = values[-1]

    if first_value == 0:
        return None

    return ((last_value - first_value) / abs(first_value)) * 100


def classify_trend(trend_pct: Optional[float], metric_type: str = "standard") -> str:
    """
    Classify trend as improving, stable, or declining.

    Args:
        trend_pct: Percentage change
        metric_type: "standard" (lower is better) or "positive" (higher is better)

    Returns:
        Classification string: "improving", "stable", or "declining"
    """
    if trend_pct is None:
        return "unknown"

    threshold = 2.0  # Consider ±2% as stable

    if metric_type == "standard":  # For mortality, readmission, CLABSI (lower is better)
        if trend_pct < -threshold:
            return "improving"
        elif trend_pct > threshold:
            return "declining"
        else:
            return "stable"
    else:  # For rating, safety score (higher is better)
        if trend_pct > threshold:
            return "improving"
        elif trend_pct < -threshold:
            return "declining"
        else:
            return "stable"


def get_hospital_trends(hospital_data: pd.DataFrame, hospital_id: int) -> Dict:
    """
    Calculate all trend metrics for a hospital.

    Args:
        hospital_data: Time-series DataFrame
        hospital_id: Hospital ID

    Returns:
        Dictionary with trend data
    """
    history = hospital_data[hospital_data['hospital_id'] == hospital_id].sort_values('year')

    if len(history) == 0:
        return {}

    metrics_to_analyze = {
        'overall_rating': 'positive',
        'mortality_rate_heart_attack': 'standard',
        'mortality_rate_pneumonia': 'standard',
        'readmission_rate': 'standard',
        'safety_score': 'positive',
        'clabsi_rate': 'standard'
    }

    trends = {
        'hospital_id': hospital_id,
        'years_available': len(history),
        'metrics': {}
    }

    years = history['year'].tolist()

    for metric, metric_type in metrics_to_analyze.items():
        if metric in history.columns:
            values = history[metric].values

            # Calculate trends for different time horizons
            trend_1yr = None
            trend_3yr = None
            trend_5yr = None

            if len(values) >= 2:
                trend_1yr = calculate_trend(values[-2:], years[-2:])

            if len(values) >= 4:
                trend_3yr = calculate_trend(values[-4:], years[-4:])

            if len(values) >= 5:
                trend_5yr = calculate_trend(values, years)

            # Classify trends
            classify = lambda t: classify_trend(t, metric_type)

            trends['metrics'][metric] = {
                'current_value': float(values[-1]) if len(values) > 0 else None,
                'previous_value': float(values[-2]) if len(values) > 1 else None,
                'trend_1yr_pct': trend_1yr,
                'trend_1yr_class': classify(trend_1yr),
                'trend_3yr_pct': trend_3yr,
                'trend_3yr_class': classify(trend_3yr),
                'trend_5yr_pct': trend_5yr,
                'trend_5yr_class': classify(trend_5yr),
                'all_values': values.tolist(),
                'all_years': years
            }

    return trends


def compare_peer_trajectories(hospital_id: int, state: str, hospital_data: pd.DataFrame) -> Dict:
    """
    Compare hospital's trend vs peer hospitals in same state.

    Args:
        hospital_id: Hospital ID
        state: State code
        hospital_data: Time-series DataFrame

    Returns:
        Comparison dictionary with rankings
    """
    # Get all hospitals in state for the most recent year
    latest_year = hospital_data['year'].max()
    state_hospitals = hospital_data[
        (hospital_data['state'] == state) & (hospital_data['year'] == latest_year)
    ]['hospital_id'].unique()

    comparison = {
        'hospital_id': hospital_id,
        'state': state,
        'peer_count': len(state_hospitals),
        'metrics': {}
    }

    # Compare each metric
    hospital_trends = get_hospital_trends(hospital_data, hospital_id)

    for metric, trend_data in hospital_trends.get('metrics', {}).items():
        trend_class = trend_data['trend_3yr_class']

        # Count peers with same trend classification
        peer_trends = []
        for peer_id in state_hospitals:
            if peer_id != hospital_id:
                peer_data = get_hospital_trends(hospital_data, peer_id)
                peer_metric_data = peer_data.get('metrics', {}).get(metric, {})
                peer_class = peer_metric_data.get('trend_3yr_class', 'unknown')
                peer_trends.append(peer_class)

        # Calculate percentile (what % of peers have better/same trend)
        better_count = sum(1 for p in peer_trends if p == 'improving' and trend_class != 'improving')
        percentile = (len(peer_trends) - better_count) / len(peer_trends) * 100 if peer_trends else 0

        comparison['metrics'][metric] = {
            'hospital_trend': trend_class,
            'peer_comparison_percentile': percentile,
            'interpretation': f"Better than {percentile:.0f}% of peers in {state}"
        }

    return comparison


def project_future_performance(hospital_data: pd.DataFrame, hospital_id: int,
                               metric: str, years_forward: int = 1) -> Optional[Dict]:
    """
    Project future performance using linear regression.

    Args:
        hospital_data: Time-series DataFrame
        hospital_id: Hospital ID
        metric: Metric to project
        years_forward: Number of years to project

    Returns:
        Projection dictionary or None if insufficient data
    """
    history = hospital_data[hospital_data['hospital_id'] == hospital_id].sort_values('year')

    if len(history) < 3 or metric not in history.columns:
        return None

    years = history['year'].values.astype(float)
    values = history[metric].values.astype(float)

    # Remove NaN values
    valid_mask = ~np.isnan(values)
    years = years[valid_mask]
    values = values[valid_mask]

    if len(years) < 2:
        return None

    # Fit linear regression
    try:
        z = np.polyfit(years, values, 1)
        p = np.poly1d(z)

        # Project
        current_year = years[-1]
        projected_years = np.arange(current_year + 1, current_year + 1 + years_forward)
        projected_values = p(projected_years)

        # Calculate uncertainty (simple std dev of residuals)
        residuals = values - p(years)
        std_error = np.std(residuals)
        confidence_interval = std_error * 1.96  # 95% CI

        return {
            'metric': metric,
            'current_value': float(values[-1]),
            'current_year': int(current_year),
            'projected_years': projected_years.astype(int).tolist(),
            'projected_values': projected_values.tolist(),
            'confidence_interval': float(confidence_interval),
            'trend_slope': float(z[0]),
            'trend_direction': 'improving' if z[0] < 0 else 'declining' if z[0] > 0 else 'stable'
        }
    except Exception as e:
        logger.warning(f"Could not project {metric} for hospital {hospital_id}: {e}")
        return None


def get_state_trend_comparison(hospital_data: pd.DataFrame, hospital_id: int,
                               state: str, year: Optional[int] = None) -> Dict:
    """
    Compare hospital's current metrics vs state average.

    Args:
        hospital_data: Time-series DataFrame
        hospital_id: Hospital ID
        state: State code
        year: Year to compare (defaults to latest)

    Returns:
        Comparison dictionary
    """
    if year is None:
        year = hospital_data['year'].max()

    state_data = hospital_data[
        (hospital_data['state'] == state) & (hospital_data['year'] == year)
    ]

    hospital_data_year = hospital_data[
        (hospital_data['hospital_id'] == hospital_id) & (hospital_data['year'] == year)
    ]

    if len(hospital_data_year) == 0 or len(state_data) == 0:
        return {}

    hospital = hospital_data_year.iloc[0]
    state_avg = state_data.mean(numeric_only=True)

    comparison = {
        'hospital_id': hospital_id,
        'state': state,
        'year': year,
        'metrics': {}
    }

    numeric_metrics = [
        'overall_rating', 'mortality_rate_heart_attack', 'mortality_rate_pneumonia',
        'readmission_rate', 'safety_score', 'clabsi_rate'
    ]

    for metric in numeric_metrics:
        if metric in hospital and metric in state_avg:
            hosp_val = float(hospital[metric])
            state_val = float(state_avg[metric])

            if state_val != 0:
                pct_diff = ((hosp_val - state_val) / abs(state_val)) * 100
            else:
                pct_diff = 0

            comparison['metrics'][metric] = {
                'hospital_value': hosp_val,
                'state_average': state_val,
                'difference': hosp_val - state_val,
                'percent_difference': pct_diff,
                'better_than_avg': (pct_diff < 0 and metric in ['mortality_rate_heart_attack', 'mortality_rate_pneumonia', 'readmission_rate', 'clabsi_rate']) or \
                                  (pct_diff > 0 and metric in ['overall_rating', 'safety_score'])
            }

    return comparison
