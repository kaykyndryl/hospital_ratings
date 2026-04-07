"""
Hybrid Analysis Agent Module

Combines rule-based longitudinal analysis with optional Azure OpenAI enhancement
and action impact estimation for comprehensive hospital performance analysis.
"""

import pandas as pd
from typing import Dict, Optional, List
import logging
import os

from utils.analysis_agent import analyze_hospital_performance, get_improvement_recommendations
from utils.longitudinal_analysis import (
    get_hospital_trends,
    compare_peer_trajectories,
    project_future_performance,
    get_state_trend_comparison
)
from utils.impact_estimator import (
    estimate_action_impact,
    generate_impact_narrative,
    prioritize_recommendations_by_impact
)

logger = logging.getLogger(__name__)


def analyze_hospital_longitudinal(hospital: pd.Series, hospital_data: pd.DataFrame,
                                  state: Optional[str] = None,
                                  include_ai_insights: bool = False) -> Dict:
    """
    Perform comprehensive longitudinal analysis of hospital performance.

    Args:
        hospital: Hospital data row
        hospital_data: Complete time-series DataFrame
        state: State code for peer comparison
        include_ai_insights: Whether to include Azure OpenAI insights (if configured)

    Returns:
        Comprehensive analysis dictionary
    """
    hospital_id = hospital['hospital_id']

    # Get basic performance analysis (existing rule-based)
    base_analysis = analyze_hospital_performance(hospital, hospital_data, state=state)

    # Get longitudinal trends
    trends = get_hospital_trends(hospital_data, hospital_id)

    # Get peer comparison
    peer_comparison = {}
    if state:
        peer_comparison = compare_peer_trajectories(hospital_id, state, hospital_data)

    # Get future projections for key metrics
    projections = {}
    for metric in ['clabsi_rate', 'readmission_rate', 'mortality_rate_heart_attack', 'overall_rating']:
        proj = project_future_performance(hospital_data, hospital_id, metric, years_forward=1)
        if proj:
            projections[metric] = proj

    # Combine into comprehensive analysis
    analysis = {
        'hospital_id': hospital_id,
        'hospital_name': hospital['name'],
        'analysis_type': 'longitudinal',
        'base_analysis': base_analysis,
        'trends': trends,
        'peer_comparison': peer_comparison,
        'projections': projections,
        'include_ai_insights': include_ai_insights
    }

    return analysis


def generate_recommendations_with_impact(hospital: pd.Series, analysis: Dict,
                                        hospital_data: pd.DataFrame) -> List[Dict]:
    """
    Generate recommendations from analysis with estimated impact metrics.

    Args:
        hospital: Hospital data row
        analysis: Analysis dictionary from analyze_hospital_longitudinal
        hospital_data: Complete time-series DataFrame

    Returns:
        List of recommendations with impact estimates
    """
    # Get base recommendations from existing analysis
    base_recommendations = get_improvement_recommendations(hospital, analysis.get('base_analysis', {}))

    # Estimate impact for each recommendation
    recommendations_with_impact = []
    for rec in base_recommendations:
        impact_estimate = estimate_action_impact(rec, hospital, hospital_data)
        rec_with_impact = {**rec, **impact_estimate}
        rec_with_impact['narrative'] = generate_impact_narrative(impact_estimate)
        recommendations_with_impact.append(rec_with_impact)

    # Prioritize by impact
    return prioritize_recommendations_by_impact(
        recommendations_with_impact, hospital, hospital_data
    )


def format_trend_summary(trends: Dict) -> str:
    """
    Format trend data into readable summary.

    Args:
        trends: Trends dictionary

    Returns:
        Formatted string summary
    """
    if not trends or 'metrics' not in trends:
        return "Insufficient data for trend analysis."

    summary_lines = []

    for metric, trend_data in trends['metrics'].items():
        current = trend_data.get('current_value')
        trend_3yr = trend_data.get('trend_3yr_pct')
        trend_class = trend_data.get('trend_3yr_class', 'unknown')

        if current is not None:
            metric_display = metric.replace('_', ' ').title()

            if trend_3yr is not None:
                direction = '↑' if trend_3yr < 0 else '↓' if trend_3yr > 0 else '→'
                summary_lines.append(
                    f"**{metric_display}**: {current:.2f} ({direction} {abs(trend_3yr):.1f}% - {trend_class})"
                )
            else:
                summary_lines.append(f"**{metric_display}**: {current:.2f}")

    return "\n".join(summary_lines)


def format_projection_summary(projections: Dict) -> str:
    """
    Format projection data into readable summary.

    Args:
        projections: Projections dictionary

    Returns:
        Formatted string summary
    """
    if not projections:
        return "Insufficient data for projections."

    summary_lines = ["**1-Year Performance Projections:**"]

    for metric, proj_data in projections.items():
        metric_display = metric.replace('_', ' ').title()
        current = proj_data.get('current_value', 0)
        projected = proj_data.get('projected_values', [])

        if projected:
            projected_val = projected[0]
            change = ((projected_val - current) / abs(current) * 100) if current != 0 else 0
            direction = '↑' if change > 0 else '↓' if change < 0 else '→'

            summary_lines.append(
                f"**{metric_display}**: {current:.2f} → {projected_val:.2f} ({direction} {abs(change):.1f}%)"
            )

    return "\n".join(summary_lines)


def format_impact_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """
    Format recommendations for display in UI.

    Args:
        recommendations: List of recommendations with impact

    Returns:
        Formatted recommendations
    """
    formatted = []

    for rec in recommendations:
        lower, upper = rec.get('estimated_improvement_range', (0, 0))

        formatted_rec = {
            'metric': rec.get('metric', ''),
            'action': rec.get('action', ''),
            'priority': rec.get('priority', 'Medium'),
            'estimated_improvement': f"{rec.get('estimated_improvement_pct', 0):.1f}%",
            'improvement_range': f"{lower:.1f}% - {upper:.1f}%",
            'confidence': rec.get('confidence_level', 'low'),
            'timeframe': rec.get('estimated_timeframe', '6-12 months'),
            'narrative': rec.get('narrative', ''),
            'details': rec.get('details', [])
        }

        formatted.append(formatted_rec)

    return formatted


def customize_analysis_for_provider(analysis: Dict, recommendations: List[Dict],
                                   state_benchmarks: Dict) -> Dict:
    """
    Customize analysis output specifically for provider decision-making.

    Args:
        analysis: Full analysis dictionary
        recommendations: Recommendations with impact
        state_benchmarks: State benchmark comparisons

    Returns:
        Provider-focused analysis
    """
    provider_analysis = {
        'executive_summary': format_trend_summary(analysis.get('trends', {})),
        'performance_projections': format_projection_summary(analysis.get('projections', {})),
        'peer_context': analysis.get('peer_comparison', {}),
        'recommended_actions': format_impact_recommendations(recommendations),
        'estimated_total_impact': sum(r.get('estimated_improvement_pct', 0) for r in recommendations) / len(recommendations) if recommendations else 0
    }

    # Add state benchmark context
    if state_benchmarks:
        provider_analysis['state_benchmarks'] = state_benchmarks

    return provider_analysis


def analyze_with_optional_ai_enhancement(hospital: pd.Series, analysis: Dict,
                                        recommendations: List[Dict]) -> Dict:
    """
    Optionally enhance analysis with Azure OpenAI if credentials are available.

    Args:
        hospital: Hospital data
        analysis: Current analysis
        recommendations: Current recommendations

    Returns:
        Enhanced analysis (or original if AI not available)
    """
    # Check if Azure OpenAI is configured
    try:
        from utils.analysis_agent import get_ai_insights
        ai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        ai_key = os.getenv('AZURE_OPENAI_API_KEY')

        if ai_endpoint and ai_key:
            # Get AI enhancement
            ai_insights = get_ai_insights(hospital, analysis, recommendations)
            analysis['ai_insights'] = ai_insights
            analysis['ai_enhanced'] = True

            logger.info(f"Enhanced analysis with AI insights for hospital {hospital['hospital_id']}")
        else:
            analysis['ai_enhanced'] = False
            logger.debug("Azure OpenAI not configured, using rule-based analysis only")

    except Exception as e:
        logger.warning(f"Could not load AI enhancement: {e}")
        analysis['ai_enhanced'] = False

    return analysis
