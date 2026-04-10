"""
Enhanced Hospital Ratings Application

Adds longitudinal analysis, trend visualization, projections, and impact-based
recommendations with 5 years of historical Medicare hospital data.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

from utils.data_loader import (
    load_historical_hospital_data,
    get_states,
    get_counties_by_state,
    filter_hospitals,
    get_star_display,
    format_percentage,
    get_hospital_details,
    get_hospital_history,
    get_available_years,
    get_summary_stats,
    get_clabsi_category,
    get_metric_color,
    get_current_year_data
)
from utils.analysis_agent import (
    analyze_hospital_performance,
    get_improvement_recommendations,
    get_peer_benchmarks,
    get_state_benchmarks
)
from utils.longitudinal_analysis import (
    get_hospital_trends,
    project_future_performance,
    get_state_trend_comparison
)
from utils.hybrid_analysis_agent import (
    analyze_hospital_longitudinal,
    generate_recommendations_with_impact,
    format_trend_summary,
    analyze_with_optional_ai_enhancement
)

# Cost estimation mapping for healthcare interventions
COST_ESTIMATES = {
    'CLABSI Rate': {
        'description': 'Central Line Bundle Implementation',
        'implementation_cost': 15000,
        'annual_cost': 8000,
        'cost_breakdown': 'Staff training ($5K), equipment ($7K), monitoring systems ($3K)'
    },
    'Readmission Rate': {
        'description': 'Discharge Planning & Follow-up Program',
        'implementation_cost': 22000,
        'annual_cost': 12000,
        'cost_breakdown': 'Care coordination staff ($12K), telehealth tools ($6K), training ($4K)'
    },
    'Mortality Rates': {
        'description': 'Clinical Pathway Review & Training',
        'implementation_cost': 18000,
        'annual_cost': 9000,
        'cost_breakdown': 'Clinical consultants ($10K), decision support ($5K), staff training ($3K)'
    },
    'Safety Score': {
        'description': 'Patient Safety Culture Program',
        'implementation_cost': 12000,
        'annual_cost': 6000,
        'cost_breakdown': 'Safety coordinator ($5K), training ($4K), systems ($3K)'
    }
}

def get_cost_estimate(metric):
    """Get cost estimate for a specific metric improvement."""
    return COST_ESTIMATES.get(metric, {
        'description': 'Process Improvement Initiative',
        'implementation_cost': 10000,
        'annual_cost': 5000,
        'cost_breakdown': 'Planning & implementation costs'
    })

# Page configuration
st.set_page_config(
    page_title="Medicare Hospital Ratings - Longitudinal Analysis",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .rating-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .metric-card {
        padding: 15px;
        border-radius: 8px;
        background-color: #e8f4f8;
        margin: 5px 0;
    }
    .hospital-header {
        padding: 15px;
        border-left: 5px solid #1f77b4;
        background-color: #f8f9fa;
        margin: 10px 0;
    }
    .trend-improving {
        color: #2ecc71;
    }
    .trend-declining {
        color: #e74c3c;
    }
    .trend-stable {
        color: #f39c12;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
df = load_historical_hospital_data()
available_years = get_available_years(df)
current_year = max(available_years) if available_years else 2024
current_year_data = get_current_year_data(df)

# Main title
st.title("🏥 Medicare Hospital Star Ratings - Longitudinal Analysis")
st.markdown("""
Comprehensive hospital performance analysis with 5-year longitudinal trends,
predictive insights, and AI-powered action recommendations with estimated impacts.
""")

st.markdown("---")

# Sidebar
st.sidebar.title("🏥 Hospital Search")
st.sidebar.markdown("---")

# Time range selector
st.sidebar.subheader("📅 Analysis Period")
year_range = st.sidebar.slider(
    "Select Year Range:",
    min_value=min(available_years),
    max_value=max(available_years),
    value=(min(available_years), current_year),
    step=1,
    key="year_range"
)

# Search filters
search_type = st.sidebar.radio(
    "Search by:",
    options=["State & County", "Hospital Name", "Rating"]
)

state = None
county = None
hospital_name = None
min_rating = None

if search_type == "State & County":
    states = get_states(current_year_data)
    state = st.sidebar.selectbox(
        "Select State:",
        options=states,
        key="state_select"
    )

    if state:
        counties = get_counties_by_state(current_year_data, state)
        county = st.sidebar.selectbox(
            "Select County:",
            options=["All Counties"] + list(counties),
            key="county_select"
        )
        if county == "All Counties":
            county = None

elif search_type == "Hospital Name":
    hospital_name = st.sidebar.text_input(
        "Enter Hospital Name:",
        placeholder="e.g., Massachusetts General"
    )

elif search_type == "Rating":
    min_rating = st.sidebar.slider(
        "Minimum Rating:",
        min_value=1.0,
        max_value=5.0,
        value=4.0,
        step=0.1
    )

# Additional filters
st.sidebar.markdown("---")
st.sidebar.subheader("Additional Filters")

filter_min_rating = st.sidebar.slider(
    "Minimum Overall Rating:",
    min_value=1.0,
    max_value=5.0,
    value=3.5,
    step=0.1,
    key="rating_filter"
) if st.sidebar.checkbox("Filter by Rating", value=False) else None

# Apply filters
filtered_df = filter_hospitals(
    current_year_data,
    state=state,
    county=county,
    hospital_name=hospital_name,
    min_rating=min_rating or filter_min_rating
)

# Display summary stats
if len(filtered_df) > 0:
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    stats = get_summary_stats(filtered_df)

    with col1:
        st.metric("Hospitals Found", stats['total_hospitals'])

    with col2:
        st.metric("Avg Rating", f"{stats['avg_rating']:.2f} ⭐")

    with col3:
        st.metric("Avg Mortality (HA)", f"{stats['avg_mortality_heart_attack']:.1f}%")

    with col4:
        st.metric("Avg Mortality (PN)", f"{stats['avg_mortality_pneumonia']:.1f}%")

    with col5:
        st.metric("Avg Readmission %", f"{stats['avg_readmission_rate']:.1f}%")

    with col6:
        st.metric("Avg CLABSI Rate", f"{stats['avg_clabsi_rate']:.2f}")

    st.markdown("---")

    # Display results table
    st.subheader(f"Results ({len(filtered_df)} hospitals)")

    display_df = filtered_df[[
        'name', 'city', 'county', 'state', 'overall_rating',
        'mortality_rate_heart_attack', 'readmission_rate', 'safety_score', 'clabsi_rate'
    ]].copy()

    display_df.columns = [
        'Hospital Name', 'City', 'County', 'State', 'Rating',
        'Mortality (HA)', 'Readmission %', 'Safety', 'CLABSI'
    ]

    display_df['Rating'] = display_df['Rating'].apply(lambda x: f"{x:.1f}⭐")
    display_df['Mortality (HA)'] = display_df['Mortality (HA)'].apply(format_percentage)
    display_df['Readmission %'] = display_df['Readmission %'].apply(format_percentage)
    display_df['Safety'] = display_df['Safety'].astype(int)
    display_df['CLABSI'] = display_df['CLABSI'].apply(lambda x: f"{x:.2f} per 1K")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Hospital detail view
    st.markdown("---")
    st.subheader("Hospital Details & Longitudinal Analysis")

    hospital_options = filtered_df['name'].tolist()
    selected_hospital = st.selectbox(
        "Select a hospital to view detailed information:",
        options=[""] + hospital_options,
        key="hospital_select"
    )

    if selected_hospital:
        hospital_id = filtered_df[filtered_df['name'] == selected_hospital].iloc[0]['hospital_id']
        hospital = get_hospital_details(current_year_data, hospital_id)

        # Display hospital header
        st.markdown(f"""
        <div class="hospital-header">
        <h3>{hospital['name']}</h3>
        <p><strong>{hospital['street_address']}</strong><br>
        {hospital['city']}, {hospital['state']} {hospital['zip_code']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Current metrics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="rating-box">
            <h4>Overall Star Rating</h4>
            <h2>{get_star_display(hospital['overall_rating'])}</h2>
            <p>Based on {int(hospital['number_of_comparisons'])} patient comparisons</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="rating-box">
            <h4>Safety Score</h4>
            <h2>{int(hospital['safety_score'])}/100</h2>
            <p>Hospital safety metrics and compliance</p>
            </div>
            """, unsafe_allow_html=True)

        st.subheader("Current Quality Metrics")

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        with metric_col1:
            st.markdown(f"""
            <div class="metric-card">
            <h4>Heart Attack Mortality</h4>
            <h3>{format_percentage(hospital['mortality_rate_heart_attack'])}</h3>
            <p style="font-size: smaller;">Patients treated for heart attacks</p>
            </div>
            """, unsafe_allow_html=True)

        with metric_col2:
            st.markdown(f"""
            <div class="metric-card">
            <h4>Pneumonia Mortality</h4>
            <h3>{format_percentage(hospital['mortality_rate_pneumonia'])}</h3>
            <p style="font-size: smaller;">Patients treated for pneumonia</p>
            </div>
            """, unsafe_allow_html=True)

        with metric_col3:
            st.markdown(f"""
            <div class="metric-card">
            <h4>Readmission Rate</h4>
            <h3>{format_percentage(hospital['readmission_rate'])}</h3>
            <p style="font-size: smaller;">Rate of patient readmissions</p>
            </div>
            """, unsafe_allow_html=True)

        with metric_col4:
            clabsi_category, clabsi_emoji = get_clabsi_category(hospital['clabsi_rate'])
            st.markdown(f"""
            <div class="metric-card">
            <h4>CLABSI Rate {clabsi_emoji}</h4>
            <h3>{hospital['clabsi_rate']:.2f}</h3>
            <p style="font-size: smaller;">Infections per 1,000 catheter days</p>
            </div>
            """, unsafe_allow_html=True)

        # Longitudinal analysis tabs
        perf_tab, trends_tab, proj_tab, rec_tab, comp_tab = st.tabs(
            ["📈 Performance", "📊 Trends", "🔮 Projections", "💡 Impact Actions", "🏥 Comparison"]
        )

        with perf_tab:
            # Current performance analysis
            analysis = analyze_hospital_performance(hospital, df, state=hospital['state'])

            if analysis:
                st.markdown(f"**{analysis.get('overall_assessment', 'Analysis')}**")

                col1, col2 = st.columns(2)

                with col1:
                    if analysis.get('strengths'):
                        st.success("**Key Strengths:**")
                        for strength in analysis['strengths']:
                            st.write(f"✅ {strength}")
                    else:
                        st.info("No metrics significantly above benchmark")

                with col2:
                    if analysis.get('weaknesses'):
                        st.error("**Areas for Improvement:**")
                        for weakness in analysis['weaknesses']:
                            st.write(f"⚠️ {weakness}")
                    else:
                        st.info("All metrics near or above benchmark")

        with trends_tab:
            # Get hospital history
            history = get_hospital_history(df, hospital_id, year_start=year_range[0], year_end=year_range[1])

            if len(history) > 1:
                st.subheader("5-Year Metric Trends")

                # Create trend charts
                metrics_to_display = [
                    ('overall_rating', 'Overall Rating'),
                    ('mortality_rate_heart_attack', 'Heart Attack Mortality %'),
                    ('mortality_rate_pneumonia', 'Pneumonia Mortality %'),
                    ('readmission_rate', 'Readmission Rate %'),
                    ('safety_score', 'Safety Score'),
                    ('clabsi_rate', 'CLABSI Rate per 1K')
                ]

                for metric, display_name in metrics_to_display:
                    if metric in history.columns:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=history['year'],
                            y=history[metric],
                            mode='lines+markers',
                            name=display_name,
                            line=dict(width=3, color='#1f77b4'),
                            marker=dict(size=8)
                        ))

                        fig.update_layout(
                            title=f"{display_name} ({year_range[0]}-{year_range[1]})",
                            xaxis_title="Year",
                            yaxis_title="Value",
                            hovermode="x unified",
                            height=350
                        )
                        fig.update_xaxes(dtick=1)

                        st.plotly_chart(fig, use_container_width=True)

                # Trend summary
                trends = get_hospital_trends(df, hospital_id)
                if trends and trends.get('metrics'):
                    st.subheader("Trend Summary")
                    st.info(format_trend_summary(trends))
            else:
                st.info("Insufficient historical data for trend analysis")

        with proj_tab:
            # Future performance projections
            st.subheader("1-Year Performance Projections")

            metrics_to_project = [
                'clabsi_rate', 'readmission_rate', 'mortality_rate_heart_attack',
                'mortality_rate_pneumonia', 'overall_rating', 'safety_score'
            ]

            projections_found = False
            for metric in metrics_to_project:
                proj = project_future_performance(df, hospital_id, metric, years_forward=1)
                if proj:
                    projections_found = True
                    current = proj['current_value']
                    projected = proj['projected_values'][0] if proj['projected_values'] else current
                    change_pct = ((projected - current) / abs(current) * 100) if current != 0 else 0

                    col1, col2 = st.columns([1, 3])

                    with col1:
                        st.metric(
                            proj['metric'].replace('_', ' ').title(),
                            f"{projected:.2f}",
                            delta=f"{change_pct:+.1f}%"
                        )

                    with col2:
                        st.write(f"Current: {current:.2f} → Projected: {projected:.2f} "
                                f"({change_pct:+.1f}%)")

            if not projections_found:
                st.info("Insufficient data for projections")

        with rec_tab:
            # Impact-based recommendations
            analysis = analyze_hospital_longitudinal(hospital, df, state=hospital['state'])
            analysis = analyze_with_optional_ai_enhancement(hospital, analysis, [])
            recommendations = generate_recommendations_with_impact(hospital, analysis, df)

            # Display AI status indicator
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Recommended Actions with Estimated Impact")
            with col2:
                ai_enhanced = analysis.get('ai_enhanced', False)
                if ai_enhanced:
                    st.success("✅ AI-Enhanced Analysis", icon="✒️")
                else:
                    st.info("🧮 Rule-Based Analysis", icon="📊")

            st.markdown("""
            Based on peer hospital performance and historical improvement patterns,
            each recommendation includes estimated impact potential and timeframe.
            """)

            # Display AI insights if available
            if ai_enhanced and analysis.get('ai_insights'):
                ai_insights = analysis['ai_insights']

                with st.expander("🤖 AI-Powered Insights from GPT", expanded=True):
                    # Executive Summary
                    if ai_insights.get('executive_summary'):
                        st.markdown("### Executive Summary")
                        summary_text = ai_insights['executive_summary']
                        st.info(summary_text)
                        st.divider()

                    # Key Insights
                    if ai_insights.get('key_insights'):
                        st.markdown("### Key Insights")
                        for insight in ai_insights['key_insights']:
                            st.write(f"• {insight}")
                        st.divider()

                    # Improvement Priorities
                    if ai_insights.get('improvement_priorities'):
                        st.markdown("### Improvement Priorities (Ranked by Impact)")
                        for idx, priority in enumerate(ai_insights['improvement_priorities'], 1):
                            st.write(f"{idx}. {priority}")
                        st.divider()

                    # Comparative Context
                    if ai_insights.get('comparative_context'):
                        st.markdown("### Comparative Context")
                        st.write(ai_insights['comparative_context'])
                        st.divider()

                    # Implementation Guidance
                    if ai_insights.get('implementation_guidance'):
                        st.markdown("### Implementation Guidance")
                        st.write(ai_insights['implementation_guidance'])

                st.markdown("---")
                st.subheader("Detailed Action Recommendations with Estimated Costs")

            if recommendations:
                total_implementation = 0
                total_annual = 0

                for idx, rec in enumerate(recommendations[:5], 1):
                    cost_data = get_cost_estimate(rec.get('metric', ''))
                    total_implementation += cost_data.get('implementation_cost', 0)
                    total_annual += cost_data.get('annual_cost', 0)

                    with st.expander(
                        f"**{idx}. {rec.get('metric', '')}: {rec.get('action', '')}** "
                        f"(Est. {rec.get('estimated_improvement_pct', 0):.1f}% improvement)",
                        expanded=(idx == 1)
                    ):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            priority = rec.get('priority', 'Medium')
                            priority_color = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(priority, '⚪')
                            st.markdown(f"**{priority_color} Priority:** {priority}")
                            st.markdown(f"**Timeframe:** {rec.get('estimated_timeframe', 'N/A')}")

                        with col2:
                            st.markdown(f"**Improvement:** {rec.get('estimated_improvement_pct', 0):.1f}%")
                            lower, upper = rec.get('estimated_improvement_range', (0, 0))
                            st.markdown(f"**Range:** {lower:.1f}% - {upper:.1f}%")

                        with col3:
                            confidence = rec.get('confidence_level', 'low')
                            confidence_icon = {'high': '📊', 'medium': '📈', 'low': '⚠️'}.get(confidence, '❓')
                            st.markdown(f"**{confidence_icon} Confidence:** {confidence.title()}")

                        st.markdown("---")
                        st.markdown(rec.get('narrative', 'Action narrative'))

                        if rec.get('details'):
                            st.markdown("**Implementation Details:**")
                            for detail in rec['details']:
                                st.write(f"• {detail}")

                        # Peer evidence
                        peer_evidence = rec.get('peer_evidence', {})
                        if peer_evidence:
                            st.markdown(f"**Evidence:** {peer_evidence.get('hospitals_improved', 0)} of "
                                       f"{peer_evidence.get('hospitals_analyzed', 0)} peer hospitals showed similar improvements")

                        # Cost information
                        st.divider()
                        st.markdown("**Estimated Costs:**")
                        cost_col1, cost_col2 = st.columns(2)
                        with cost_col1:
                            st.metric("Implementation Cost", f"${cost_data.get('implementation_cost', 0):,}")
                        with cost_col2:
                            st.metric("Annual Operating Cost", f"${cost_data.get('annual_cost', 0):,}")
                        st.caption(f"Cost Breakdown: {cost_data.get('cost_breakdown', 'N/A')}")

                # Display total costs
                st.markdown("---")
                st.subheader("Total Investment Summary")
                sum_col1, sum_col2, sum_col3 = st.columns(3)
                with sum_col1:
                    st.metric("Total Implementation Cost", f"${total_implementation:,}")
                with sum_col2:
                    st.metric("Total Annual Cost", f"${total_annual:,}")
                with sum_col3:
                    st.metric("ROI Timeframe", "12-24 months")
                st.info(f"💡 Estimated total investment of ${total_implementation:,} with ${total_annual:,} annual operating costs "
                       f"for all {len(recommendations[:5])} recommended improvements.")

            else:
                st.info("No recommendations available")

        with comp_tab:
            # Hospital comparison
            st.subheader("Compare with Peer Hospitals")

            state_hospitals = current_year_data[current_year_data['state'] == hospital['state']]['name'].unique()
            state_hospitals = [h for h in state_hospitals if h != hospital['name']]

            if state_hospitals:
                compare_hospitals = st.multiselect(
                    "Select hospitals to compare:",
                    options=state_hospitals,
                    max_selections=2,
                    help="You can select only 2 hospitals to compare",
                    key="comparison_select"
                )

                if compare_hospitals:
                    with st.status("🔍 Analyzing hospital comparison data...", expanded=True) as status:
                        comparison_list = [hospital.to_dict()]

                        for comp_name in compare_hospitals:
                            comp_id = current_year_data[current_year_data['name'] == comp_name].iloc[0]['hospital_id']
                            comp_data = get_hospital_details(current_year_data, comp_id)
                            comparison_list.append(comp_data.to_dict())

                        # Create comparison visualization
                        metrics_to_compare = [
                            ('overall_rating', 'Overall Rating'),
                            ('safety_score', 'Safety Score'),
                            ('mortality_rate_heart_attack', 'Mortality (Heart Attack)'),
                            ('readmission_rate', 'Readmission Rate'),
                            ('clabsi_rate', 'CLABSI Rate')
                        ]

                        # Prepare data for comparison chart
                        chart_data = []
                        for metric, display_name in metrics_to_compare:
                            row = {'Metric': display_name}
                            for hosp in comparison_list:
                                row[hosp.get('name', 'Unknown')] = float(hosp.get(metric, 0))
                            chart_data.append(row)

                        comparison_df = pd.DataFrame(chart_data)
                        status.update(label="✅ Analysis complete!", state="complete")

                    fig = px.bar(
                        comparison_df,
                        x='Metric',
                        y=[h.get('name', 'Unknown') for h in comparison_list],
                        barmode='group',
                        title='Hospital Metrics Comparison'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

                    st.subheader("Detailed Comparison Table")
                    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            else:
                st.info("No other hospitals in this state to compare")

else:
    st.warning("No hospitals found matching your search criteria. Try adjusting your filters.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: small;">
<p>Data-driven insights combining 5 years of historical Medicare Hospital Compare data</p>
<p>Impact estimates based on peer hospital performance patterns and clinical literature</p>
<p>For current data, visit <a href="https://www.Medicare.gov/care-compare/" target="_blank">Medicare.gov/care-compare/</a></p>
</div>
""", unsafe_allow_html=True)
