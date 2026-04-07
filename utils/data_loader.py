import pandas as pd
from pathlib import Path
import streamlit as st


@st.cache_data
def load_hospital_data():
    """Load hospital ratings data from CSV."""
    data_path = Path(__file__).parent.parent / "data" / "hospital_ratings.csv"
    return pd.read_csv(data_path)


@st.cache_data
def load_historical_hospital_data():
    """Load historical time-series hospital ratings data (5 years)."""
    data_path = Path(__file__).parent.parent / "data" / "processed" / "hospital_timeseries.csv"
    if data_path.exists():
        df = pd.read_csv(data_path)
        # Ensure year column is present
        if 'year' not in df.columns:
            df['year'] = 2024  # Default to current year if missing
        return df
    else:
        # Fallback: use single-year data
        return load_hospital_data()


def get_states(df):
    """Get unique states sorted alphabetically."""
    return sorted(df['state'].unique())


def get_counties_by_state(df, state):
    """Get unique counties for a given state, sorted alphabetically."""
    counties = df[df['state'] == state]['county'].unique()
    return sorted(counties)


def filter_hospitals(df, state=None, county=None, hospital_name=None, min_rating=None):
    """Filter hospitals based on search criteria."""
    filtered_df = df.copy()

    if state:
        filtered_df = filtered_df[filtered_df['state'] == state]

    if county:
        filtered_df = filtered_df[filtered_df['county'] == county]

    if hospital_name:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(hospital_name, case=False, na=False)
        ]

    if min_rating:
        filtered_df = filtered_df[filtered_df['overall_rating'] >= min_rating]

    return filtered_df.sort_values('overall_rating', ascending=False)


def get_star_display(rating):
    """Convert numeric rating to star display."""
    full_stars = int(rating)
    half_star = rating - full_stars >= 0.5

    stars = "⭐" * full_stars
    if half_star and full_stars < 5:
        stars += "✨"

    return f"{stars} {rating:.1f}/5.0"


def format_percentage(value):
    """Format value as percentage."""
    return f"{value:.1f}%"


def get_hospital_details(df, hospital_id):
    """Get full details for a specific hospital."""
    return df[df['hospital_id'] == hospital_id].iloc[0]


def get_summary_stats(df):
    """Get summary statistics for filtered results."""
    if len(df) == 0:
        return None

    return {
        'total_hospitals': len(df),
        'avg_rating': df['overall_rating'].mean(),
        'avg_mortality_heart_attack': df['mortality_rate_heart_attack'].mean(),
        'avg_mortality_pneumonia': df['mortality_rate_pneumonia'].mean(),
        'avg_readmission_rate': df['readmission_rate'].mean(),
        'avg_clabsi_rate': df['clabsi_rate'].mean(),
        'avg_safety_score': df['safety_score'].mean(),
    }


def get_summary_stats_extended(df):
    """Get extended summary statistics including CLABSI metrics."""
    if len(df) == 0:
        return None

    return {
        'total_hospitals': len(df),
        'avg_rating': df['overall_rating'].mean(),
        'min_rating': df['overall_rating'].min(),
        'max_rating': df['overall_rating'].max(),
        'avg_mortality_heart_attack': df['mortality_rate_heart_attack'].mean(),
        'avg_mortality_pneumonia': df['mortality_rate_pneumonia'].mean(),
        'avg_readmission_rate': df['readmission_rate'].mean(),
        'avg_clabsi_rate': df['clabsi_rate'].mean(),
        'min_clabsi_rate': df['clabsi_rate'].min(),
        'max_clabsi_rate': df['clabsi_rate'].max(),
        'avg_safety_score': df['safety_score'].mean(),
    }


def get_clabsi_category(clabsi_rate):
    """Categorize CLABSI rate performance."""
    if clabsi_rate <= 0.8:
        return ('Excellent', '🟢')
    elif clabsi_rate <= 1.0:
        return ('Good', '🟡')
    elif clabsi_rate <= 1.3:
        return ('Fair', '🟠')
    else:
        return ('Poor', '🔴')


def get_metric_color(category):
    """Get color for metric category."""
    colors = {
        'Excellent': '#2ecc71',  # Green
        'Good': '#3498db',       # Blue
        'Fair': '#f39c12',       # Orange
        'Poor': '#e74c3c',       # Red
    }
    return colors.get(category, '#95a5a6')


def get_available_years(df):
    """Get sorted list of available years in historical data."""
    if 'year' in df.columns:
        return sorted(df['year'].unique())
    return [2024]


def get_hospital_history(df, hospital_id, year_start=None, year_end=None):
    """
    Get historical data for a specific hospital over a time range.

    Args:
        df: Time-series DataFrame
        hospital_id: ID of hospital
        year_start: Starting year (inclusive)
        year_end: Ending year (inclusive)

    Returns:
        DataFrame with hospital's history, sorted by year
    """
    history = df[df['hospital_id'] == hospital_id].copy()

    if year_start is not None:
        history = history[history['year'] >= year_start]

    if year_end is not None:
        history = history[history['year'] <= year_end]

    return history.sort_values('year')


def get_hospital_by_year(df, hospital_id, year):
    """Get hospital data for a specific year."""
    result = df[(df['hospital_id'] == hospital_id) & (df['year'] == year)]
    if len(result) > 0:
        return result.iloc[0]
    return None


def get_hospitals_by_year(df, year=None):
    """Get all hospitals for a specific year."""
    if year is None:
        years = get_available_years(df)
        year = max(years) if years else 2024

    return df[df['year'] == year].copy()


def get_current_year_data(df):
    """Get hospital data for the most recent year available."""
    years = get_available_years(df)
    if years:
        return df[df['year'] == max(years)]
    return df
