"""
Analysis engine for hospital performance with rule-based insights.
Provides root cause analysis and improvement recommendations.

OpenRouter API integration for AI-enhanced analysis.
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _categorize_performance(value, benchmark, is_lower_better=True):
    """Categorize performance as Excellent, Good, Fair, or Poor."""
    if is_lower_better:
        if value <= benchmark * 0.80:
            return "Excellent"
        elif value <= benchmark * 0.95:
            return "Good"
        elif value <= benchmark * 1.10:
            return "Fair"
        else:
            return "Poor"
    else:
        if value >= benchmark * 1.20:
            return "Excellent"
        elif value >= benchmark * 1.05:
            return "Good"
        elif value >= benchmark * 0.90:
            return "Fair"
        else:
            return "Poor"


def get_peer_benchmarks(df):
    """Calculate benchmarks for all key metrics."""
    return {
        'overall_rating': df['overall_rating'].mean(),
        'mortality_heart_attack': df['mortality_rate_heart_attack'].mean(),
        'mortality_pneumonia': df['mortality_rate_pneumonia'].mean(),
        'readmission_rate': df['readmission_rate'].mean(),
        'safety_score': df['safety_score'].mean(),
        'clabsi_rate': df['clabsi_rate'].mean(),
    }


def get_state_benchmarks(df, state):
    """Calculate benchmarks for hospitals in specific state."""
    state_df = df[df['state'] == state]
    if len(state_df) == 0:
        return None

    return {
        'overall_rating': state_df['overall_rating'].mean(),
        'mortality_heart_attack': state_df['mortality_rate_heart_attack'].mean(),
        'mortality_pneumonia': state_df['mortality_rate_pneumonia'].mean(),
        'readmission_rate': state_df['readmission_rate'].mean(),
        'safety_score': state_df['safety_score'].mean(),
        'clabsi_rate': state_df['clabsi_rate'].mean(),
    }


def analyze_hospital_performance(hospital, df, state=None):
    """
    Analyze hospital performance and identify strengths/weaknesses.
    Returns detailed analysis with root causes.
    """
    if state:
        benchmarks = get_state_benchmarks(df, state)
        benchmark_type = f"state ({state})"
    else:
        benchmarks = get_peer_benchmarks(df)
        benchmark_type = "national"

    if benchmarks is None:
        return None

    analysis = {
        'hospital_name': hospital['name'],
        'benchmark_type': benchmark_type,
        'metrics': {},
        'overall_assessment': '',
        'strengths': [],
        'weaknesses': [],
        'root_causes': [],
    }

    # Analyze each metric
    metrics_analysis = {
        'Overall Rating': {
            'value': hospital['overall_rating'],
            'benchmark': benchmarks['overall_rating'],
            'is_lower_better': False,
            'unit': 'stars'
        },
        'Heart Attack Mortality': {
            'value': hospital['mortality_rate_heart_attack'],
            'benchmark': benchmarks['mortality_heart_attack'],
            'is_lower_better': True,
            'unit': '%'
        },
        'Pneumonia Mortality': {
            'value': hospital['mortality_rate_pneumonia'],
            'benchmark': benchmarks['mortality_pneumonia'],
            'is_lower_better': True,
            'unit': '%'
        },
        'Readmission Rate': {
            'value': hospital['readmission_rate'],
            'benchmark': benchmarks['readmission_rate'],
            'is_lower_better': True,
            'unit': '%'
        },
        'Safety Score': {
            'value': hospital['safety_score'],
            'benchmark': benchmarks['safety_score'],
            'is_lower_better': False,
            'unit': '/100'
        },
        'CLABSI Rate': {
            'value': hospital['clabsi_rate'],
            'benchmark': benchmarks['clabsi_rate'],
            'is_lower_better': True,
            'unit': 'per 1K catheter days'
        }
    }

    for metric_name, metric_data in metrics_analysis.items():
        category = _categorize_performance(
            metric_data['value'],
            metric_data['benchmark'],
            metric_data['is_lower_better']
        )

        performance_vs_benchmark = (
            (metric_data['value'] - metric_data['benchmark']) / metric_data['benchmark'] * 100
            if metric_data['benchmark'] != 0 else 0
        )

        analysis['metrics'][metric_name] = {
            'value': metric_data['value'],
            'benchmark': metric_data['benchmark'],
            'category': category,
            'vs_benchmark_pct': performance_vs_benchmark,
            'unit': metric_data['unit']
        }

        if category == 'Excellent':
            analysis['strengths'].append(metric_name)
        elif category == 'Poor':
            analysis['weaknesses'].append(metric_name)

    # Identify patterns and root causes
    analysis['root_causes'] = _identify_root_causes(hospital, analysis)

    # Generate overall assessment
    num_excellent = len([m for m in analysis['metrics'].values() if m['category'] == 'Excellent'])
    num_poor = len([m for m in analysis['metrics'].values() if m['category'] == 'Poor'])

    if num_poor == 0:
        analysis['overall_assessment'] = 'Strong performer with consistent quality across metrics'
    elif num_poor >= 3:
        analysis['overall_assessment'] = 'Multiple quality concerns require systematic improvement initiatives'
    elif num_poor >= 2:
        analysis['overall_assessment'] = 'Several areas need improvement across operational processes'
    else:
        analysis['overall_assessment'] = 'Generally good performance with some focused improvement opportunities'

    return analysis


def _identify_root_causes(hospital, analysis):
    """Identify potential root causes based on metric patterns."""
    root_causes = []

    weak_metrics = [m for m, data in analysis['metrics'].items() if data['category'] == 'Poor']

    # Specific root cause patterns
    if 'CLABSI Rate' in weak_metrics and 'Safety Score' in weak_metrics:
        root_causes.append(
            "Multiple safety concerns suggest infrastructure/training issues: "
            "Review clinical protocols, staff education, and infection control procedures"
        )

    if 'Readmission Rate' in weak_metrics and 'CLABSI Rate' in weak_metrics:
        root_causes.append(
            "Post-acute care coordination gaps: Patients may be discharged prematurely or "
            "without adequate follow-up planning, leading to readmissions and infections"
        )

    if 'Heart Attack Mortality' in weak_metrics or 'Pneumonia Mortality' in weak_metrics:
        root_causes.append(
            "Clinical pathway concerns: Review diagnostic protocols, specialist availability, "
            "and patient risk stratification for targeted conditions"
        )

    if 'Readmission Rate' in weak_metrics:
        root_causes.append(
            "Discharge planning deficiencies: Enhanced medication reconciliation and "
            "follow-up care coordination needed"
        )

    if 'CLABSI Rate' in weak_metrics:
        root_causes.append(
            "Central line infection prevention gaps: Implement evidence-based bundles, "
            "increase staff training, and strengthen compliance monitoring"
        )

    if hospital['safety_score'] < 80:
        root_causes.append(
            "Systematic safety culture improvements needed across multiple domains"
        )

    return root_causes if root_causes else [
        "Metrics are close to benchmark - focus on incremental improvements"
    ]


def get_improvement_recommendations(hospital, analysis):
    """
    Generate specific, actionable improvement recommendations.
    """
    recommendations = []

    # High-priority recommendations based on worst metrics
    poor_metrics = {m: data for m, data in analysis['metrics'].items() if data['category'] == 'Poor'}
    fair_metrics = {m: data for m, data in analysis['metrics'].items() if data['category'] == 'Fair'}

    # CLABSI-specific
    if 'CLABSI Rate' in poor_metrics:
        recommendations.append({
            'priority': 'High',
            'metric': 'CLABSI Rate',
            'action': 'Implement Central Line Bundle protocol',
            'details': [
                'Daily line necessity review by clinical team',
                'Prompt removal of unnecessary lines',
                'Aseptic insertion and maintenance procedures training',
                'Daily catheter site review and documentation',
                'Staff certification program for line insertion/maintenance'
            ]
        })

    # Readmission rate
    if 'Readmission Rate' in poor_metrics:
        recommendations.append({
            'priority': 'High',
            'metric': 'Readmission Rate',
            'action': 'Strengthen Discharge Planning',
            'details': [
                'Implement structured discharge checklist',
                'Ensure medication reconciliation within 24 hours',
                'Schedule post-discharge follow-up appointments before discharge',
                'Provide clear discharge instructions and medication list',
                'Consider hospital-to-home transition programs for high-risk patients'
            ]
        })

    # Mortality rates
    if 'Heart Attack Mortality' in poor_metrics or 'Pneumonia Mortality' in poor_metrics:
        recommendations.append({
            'priority': 'High',
            'metric': 'Mortality Rates',
            'action': 'Review Clinical Pathways',
            'details': [
                'Audit current treatment protocols against best practices',
                'Ensure access to cardiology/pulmonology specialists',
                'Review triage and initial assessment procedures',
                'Implement evidence-based clinical decision support tools',
                'Analyze case outcomes for improvement opportunities'
            ]
        })

    # Safety score
    if hospital['safety_score'] < 85:
        recommendations.append({
            'priority': 'Medium',
            'metric': 'Safety Score',
            'action': 'Enhance Patient Safety Culture',
            'details': [
                'Conduct systematic safety audit across departments',
                'Increase incident reporting and near-miss analysis',
                'Implement safety committee review meetings',
                'Provide patient safety training to all staff',
                'Use incident data to drive process improvements'
            ]
        })

    # Fair metrics - improvement opportunities
    if 'Readmission Rate' in fair_metrics and 'Readmission Rate' not in poor_metrics:
        recommendations.append({
            'priority': 'Medium',
            'metric': 'Readmission Rate',
            'action': 'Optimize Post-Discharge Care',
            'details': [
                'Expand telehealth follow-up capability',
                'Increase nursing home communication protocols',
                'Create patient-specific discharge plans',
                'Monitor early warning signs for complications'
            ]
        })

    # If no specific issues, provide general optimizations
    if not recommendations:
        recommendations.append({
            'priority': 'Low',
            'metric': 'General',
            'action': 'Continuous Quality Improvement',
            'details': [
                'Implement benchmarking program for peer comparison',
                'Regular review of quality initiatives and outcomes',
                'Staff recognition for quality improvements',
                'Invest in training and development programs',
                'Engage physician leadership in quality initiatives'
            ]
        })

    return recommendations


def get_performance_summary(hospital, analysis):
    """Generate human-readable performance summary."""
    summary = f"""
**{hospital['name']}**

Overall Assessment: {analysis['overall_assessment']}

Key Strengths ({len(analysis['strengths'])} metrics):
"""
    if analysis['strengths']:
        for strength in analysis['strengths']:
            summary += f"\n• {strength}"
    else:
        summary += "\n• Performing at or near benchmark across most metrics"

    summary += f"\n\nAreas for Improvement ({len(analysis['weaknesses'])} metrics):"
    if analysis['weaknesses']:
        for weakness in analysis['weaknesses']:
            summary += f"\n• {weakness}"
    else:
        summary += "\n• No areas significantly below benchmark"

    summary += f"\n\nRoot Cause Analysis:"
    for i, cause in enumerate(analysis['root_causes'], 1):
        summary += f"\n{i}. {cause}"

    return summary


# ================================================================================
# OpenRouter API Integration for AI-Enhanced Analysis
# ================================================================================

def _get_openrouter_client():
    """Create OpenRouter client from environment variables."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError(
            "Missing OpenRouter API key. "
            "Please set OPENROUTER_API_KEY in .env file. "
            "You can also set it directly: OPENROUTER_API_KEY=sk-or-v1-..."
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def _prepare_hospital_context(hospital: Dict, df: pd.DataFrame, state: str) -> str:
    """Prepare hospital data for AI analysis."""
    state_benchmarks = df[df['state'] == state].agg({
        'overall_rating': 'mean',
        'mortality_rate_heart_attack': 'mean',
        'mortality_rate_pneumonia': 'mean',
        'readmission_rate': 'mean',
        'safety_score': 'mean',
        'clabsi_rate': 'mean'
    })

    national_benchmarks = df.agg({
        'overall_rating': 'mean',
        'mortality_rate_heart_attack': 'mean',
        'mortality_rate_pneumonia': 'mean',
        'readmission_rate': 'mean',
        'safety_score': 'mean',
        'clabsi_rate': 'mean'
    })

    context = f"""
Hospital Performance Data:
- Hospital: {hospital['name']}
- Location: {hospital.get('city', 'N/A')}, {hospital.get('state', 'N/A')}
- Overall Rating: {hospital['overall_rating']:.1f} stars

Quality Metrics:
- Heart Attack Mortality: {hospital['mortality_rate_heart_attack']:.2f}% (State Avg: {state_benchmarks['mortality_rate_heart_attack']:.2f}%, National: {national_benchmarks['mortality_rate_heart_attack']:.2f}%)
- Pneumonia Mortality: {hospital['mortality_rate_pneumonia']:.2f}% (State Avg: {state_benchmarks['mortality_rate_pneumonia']:.2f}%, National: {national_benchmarks['mortality_rate_pneumonia']:.2f}%)
- Readmission Rate: {hospital['readmission_rate']:.2f}% (State Avg: {state_benchmarks['readmission_rate']:.2f}%, National: {national_benchmarks['readmission_rate']:.2f}%)
- Safety Score: {hospital['safety_score']:.0f}/100 (State Avg: {state_benchmarks['safety_score']:.0f}, National: {national_benchmarks['safety_score']:.0f})
- CLABSI Rate: {hospital['clabsi_rate']:.2f} per 1K catheter days (State Avg: {state_benchmarks['clabsi_rate']:.2f}, National: {national_benchmarks['clabsi_rate']:.2f})
"""
    return context


def get_ai_insights(hospital: Dict, analysis: Dict, recommendations: List[Dict]) -> Optional[Dict]:
    """Use OpenRouter API to generate AI insights for hospital recommendations."""
    state = hospital.get('state', 'N/A')

    try:
        client = _get_openrouter_client()
    except ValueError as e:
        logger.warning(f"OpenRouter not configured: {e}")
        return None

    # Prepare context from base analysis
    base_analysis = analysis.get('base_analysis', {})
    hospital_data = analysis.get('hospital_data', {})

    prompt = f"""Analyze the following hospital's Medicare quality metrics and provide deep insights for AI-enhanced recommendations.

Hospital: {hospital['name']}
State: {state}
Overall Rating: {hospital['overall_rating']:.1f} stars

Current Performance Metrics:
- Heart Attack Mortality: {hospital['mortality_rate_heart_attack']:.2f}%
- Pneumonia Mortality: {hospital['mortality_rate_pneumonia']:.2f}%
- Readmission Rate: {hospital['readmission_rate']:.2f}%
- Safety Score: {hospital['safety_score']:.0f}/100
- CLABSI Rate: {hospital['clabsi_rate']:.2f} per 1K catheter days

Existing Analysis:
- Overall Assessment: {base_analysis.get('overall_assessment', 'N/A')}
- Strengths: {', '.join(base_analysis.get('strengths', []))}
- Weaknesses: {', '.join(base_analysis.get('weaknesses', []))}

Provide analysis in JSON format:
{{
    "executive_summary": "1-2 sentence synthesis of hospital performance",
    "key_insights": ["2-3 specific, actionable insights"],
    "improvement_priorities": ["Top 3 improvement opportunities ranked by impact"],
    "comparative_context": "How this hospital compares to peers and benchmarks",
    "implementation_guidance": "Practical steps for each priority improvement"
}}

Be specific, data-driven, and focused on actionable outcomes."""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert healthcare quality analyst with deep knowledge of Medicare quality metrics, patient safety, and hospital operations. Provide detailed, actionable analysis based on metric patterns and evidence-based practices."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1500
        )

        analysis_text = response.choices[0].message.content
        try:
            ai_insights = json.loads(analysis_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, wrap the response
            ai_insights = {
                "executive_summary": analysis_text,
                "key_insights": [],
                "improvement_priorities": [],
                "comparative_context": "",
                "implementation_guidance": ""
            }

        logger.info(f"Generated AI insights for hospital {hospital.get('hospital_id', 'unknown')}")
        return ai_insights

    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {str(e)}")
        return None
