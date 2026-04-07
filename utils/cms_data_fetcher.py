"""
CMS Hospital Compare Data Fetcher

Fetches and manages historical Medicare hospital data from CMS public datasets.
Supports fetching 5 years of data and consolidating into time-series format.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Base directory for all hospital data
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "cms_downloads"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


# CMS field mapping - maps year-specific column names to standardized names
CMS_COLUMN_MAPPING = {
    "Facility ID": "hospital_id",
    "Facility Name": "name",
    "Address": "street_address",
    "City": "city",
    "County Name": "county",
    "State": "state",
    "ZIP Code": "zip_code",
    "Overall Star Rating": "overall_rating",
    "Mortality - Heart Attack": "mortality_rate_heart_attack",
    "Mortality - Pneumonia": "mortality_rate_pneumonia",
    "Readmission - All Patients": "readmission_rate",
    "Safety Grade": "safety_score",
    "Number of Comparisons": "number_of_comparisons",
    "CLABSI Rate": "clabsi_rate",
}

# Alternative column names for older data formats
CMS_COLUMN_MAPPING_ALT = {
    "Provider ID": "hospital_id",
    "Provider Name": "name",
    "Street Address": "street_address",
    "ZIP code": "zip_code",
    "State Code": "state",
    "Hospital overall rating": "overall_rating",
    "Mortality Rate - Heart Attack": "mortality_rate_heart_attack",
    "Mortality Rate - Pneumonia": "mortality_rate_pneumonia",
    "Readmission Rate": "readmission_rate",
    "Hospital Safety Grade": "safety_score",
    "Number of Comparisons": "number_of_comparisons",
    "Central Line Bloodstream Infection Rate": "clabsi_rate",
}


def get_expected_columns() -> list:
    """Get list of expected standardized columns."""
    return [
        "hospital_id",
        "name",
        "street_address",
        "city",
        "county",
        "state",
        "zip_code",
        "overall_rating",
        "mortality_rate_heart_attack",
        "mortality_rate_pneumonia",
        "readmission_rate",
        "safety_score",
        "number_of_comparisons",
        "clabsi_rate",
    ]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names from CMS download to standardized format.
    Handles both current and legacy CMS data formats.
    """
    # Try primary mapping
    for cms_col, std_col in CMS_COLUMN_MAPPING.items():
        if cms_col in df.columns:
            df = df.rename(columns={cms_col: std_col})

    # Try alternative mappings
    for cms_col, std_col in CMS_COLUMN_MAPPING_ALT.items():
        if cms_col in df.columns and std_col not in df.columns:
            df = df.rename(columns={cms_col: std_col})

    return df


def validate_csv_format(df: pd.DataFrame) -> tuple[bool, str]:
    """
    Validate that CSV has required columns and correct data types.

    Returns:
        (is_valid, message)
    """
    expected_cols = get_expected_columns()
    missing_cols = [col for col in expected_cols if col not in df.columns]

    if missing_cols:
        return False, f"Missing columns: {missing_cols}"

    # Validate data types (numeric columns should be numeric)
    numeric_cols = [
        "hospital_id", "overall_rating", "mortality_rate_heart_attack",
        "mortality_rate_pneumonia", "readmission_rate", "safety_score",
        "number_of_comparisons", "clabsi_rate"
    ]

    for col in numeric_cols:
        try:
            pd.to_numeric(df[col], errors="coerce")
        except Exception as e:
            return False, f"Column {col} cannot be converted to numeric: {e}"

    return True, "Valid"


def load_cms_csv(file_path: str, year: int) -> Optional[pd.DataFrame]:
    """
    Load and validate a CMS Hospital Compare CSV file.

    Args:
        file_path: Path to CSV file
        year: Year of data (for validation)

    Returns:
        Cleaned DataFrame or None if validation fails
    """
    try:
        df = pd.read_csv(file_path)

        # Normalize columns
        df = normalize_columns(df)

        # Validate format
        is_valid, message = validate_csv_format(df)
        if not is_valid:
            logger.error(f"Validation failed for {year} data: {message}")
            return None

        # Convert numeric columns
        numeric_cols = [
            "hospital_id", "overall_rating", "mortality_rate_heart_attack",
            "mortality_rate_pneumonia", "readmission_rate", "safety_score",
            "number_of_comparisons", "clabsi_rate"
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Ensure state is uppercase
        if "state" in df.columns:
            df["state"] = df["state"].str.upper()

        # Add year column
        df["year"] = year

        logger.info(f"Successfully loaded {len(df)} hospitals for year {year}")
        return df

    except Exception as e:
        logger.error(f"Error loading CSV from {file_path}: {e}")
        return None


def merge_years(year_dfs: Dict[int, pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple years of hospital data into single time-series DataFrame.

    Args:
        year_dfs: Dictionary mapping year -> DataFrame

    Returns:
        Consolidated DataFrame with all years
    """
    dfs = [df for year, df in sorted(year_dfs.items()) if df is not None]

    if not dfs:
        raise ValueError("No valid DataFrames to merge")

    combined_df = pd.concat(dfs, ignore_index=True)

    # Ensure consistent column order
    expected_cols = get_expected_columns() + ["year"]
    existing_cols = [col for col in expected_cols if col in combined_df.columns]
    combined_df = combined_df[existing_cols]

    logger.info(f"Merged {len(year_dfs)} years into {len(combined_df)} total records")
    return combined_df


def calculate_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate trend metrics (1yr, 3yr, 5yr % change) for each hospital.

    Args:
        df: Time-series DataFrame with year column

    Returns:
        DataFrame with additional trend columns
    """
    metrics = [
        "overall_rating",
        "mortality_rate_heart_attack",
        "mortality_rate_pneumonia",
        "readmission_rate",
        "safety_score",
        "clabsi_rate"
    ]

    # For each hospital, calculate trends
    for metric in metrics:
        df[f"{metric}_trend_1yr"] = np.nan
        df[f"{metric}_trend_3yr"] = np.nan
        df[f"{metric}_trend_5yr"] = np.nan

    # Group by hospital and calculate trends
    for hospital_id, group in df.groupby("hospital_id"):
        group_sorted = group.sort_values("year")
        values_by_year = dict(zip(group_sorted["year"], group_sorted.index))

        for metric in metrics:
            metric_values = group_sorted[metric].values
            years = group_sorted["year"].values

            for idx, row_idx in enumerate(group_sorted.index):
                current_year = df.loc[row_idx, "year"]
                current_value = df.loc[row_idx, metric]

                # 1-year trend
                if idx > 0:
                    prev_value = group_sorted[metric].iloc[idx - 1]
                    if pd.notna(prev_value) and current_value != 0:
                        trend = ((current_value - prev_value) / abs(prev_value)) * 100
                        df.loc[row_idx, f"{metric}_trend_1yr"] = trend

                # 3-year trend
                three_yr_back = current_year - 3
                matching_rows = group_sorted[group_sorted["year"] >= three_yr_back]
                if len(matching_rows) > 0:
                    early_value = matching_rows[metric].iloc[0]
                    if pd.notna(early_value) and current_value != 0:
                        trend = ((current_value - early_value) / abs(early_value)) * 100
                        df.loc[row_idx, f"{metric}_trend_3yr"] = trend

                # 5-year trend
                five_yr_back = current_year - 5
                matching_rows = group_sorted[group_sorted["year"] >= five_yr_back]
                if len(matching_rows) > 0:
                    early_value = matching_rows[metric].iloc[0]
                    if pd.notna(early_value) and current_value != 0:
                        trend = ((current_value - early_value) / abs(early_value)) * 100
                        df.loc[row_idx, f"{metric}_trend_5yr"] = trend

    return df


def load_historical_data_from_csvs(csv_paths: Dict[int, str]) -> Optional[pd.DataFrame]:
    """
    Load historical data from multiple CSV files (one per year).

    Args:
        csv_paths: Dictionary mapping year -> file path
                   Example: {2020: "path/to/2020.csv", 2021: "path/to/2021.csv"}

    Returns:
        Consolidated time-series DataFrame or None if no valid data
    """
    year_dfs = {}

    for year, file_path in csv_paths.items():
        df = load_cms_csv(file_path, year)
        if df is not None:
            year_dfs[year] = df

    if not year_dfs:
        logger.error("No valid data files loaded")
        return None

    combined_df = merge_years(year_dfs)
    combined_df = calculate_trends(combined_df)

    return combined_df


def save_processed_data(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Save consolidated time-series data to CSV.

    Args:
        df: DataFrame to save
        output_path: Optional custom output path

    Returns:
        Path where data was saved
    """
    if output_path is None:
        output_path = PROCESSED_DATA_DIR / "hospital_timeseries.csv"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

    return str(output_path)


def get_processed_data_path() -> Path:
    """Get path to processed time-series data."""
    return PROCESSED_DATA_DIR / "hospital_timeseries.csv"


def data_exists() -> bool:
    """Check if processed time-series data exists."""
    return get_processed_data_path().exists()


def get_data_freshness() -> Optional[str]:
    """Get modification time of processed data (for UI display)."""
    path = get_processed_data_path()
    if path.exists():
        mtime = os.path.getmtime(path)
        from datetime import datetime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    return None
