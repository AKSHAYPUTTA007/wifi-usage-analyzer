# =============================================================
# utils.py — Utility / Helper Functions
# Wi-Fi Usage Analyzer
# =============================================================
# This module contains reusable helper functions that are
# used by both analysis.py and ui.py.
#
# Rules:
#   - No Tkinter imports here (keep UI separate).
#   - No Pandas analysis logic here (keep it in analysis.py).
#   - Only pure utility functions: formatting, validation, etc.
# =============================================================

import os
import pandas as pd
from config import (
    MANDATORY_COLUMNS,
    OPTIONAL_COLUMNS,
    ALL_COLUMNS,
    COL_TIMESTAMP,
)


# =============================================================
# Column Compatibility
# =============================================================

def check_columns(df: pd.DataFrame) -> dict:
    """
    Check which expected columns are present in the dataframe.

    Returns a dictionary with:
        - 'missing_mandatory' : list of mandatory columns not found
        - 'present_optional'  : list of optional columns found
        - 'missing_optional'  : list of optional columns not found
        - 'is_valid'          : True if all mandatory columns exist
        - 'extra_columns'     : columns in the file not in our schema

    Parameters:
        df (pd.DataFrame): The loaded dataset.

    Returns:
        dict: Compatibility report.
    """

    actual_columns = list(df.columns)

    missing_mandatory = [
        col for col in MANDATORY_COLUMNS
        if col not in actual_columns
    ]

    present_optional = [
        col for col in OPTIONAL_COLUMNS
        if col in actual_columns
    ]

    missing_optional = [
        col for col in OPTIONAL_COLUMNS
        if col not in actual_columns
    ]

    extra_columns = [
        col for col in actual_columns
        if col not in ALL_COLUMNS
    ]

    is_valid = len(missing_mandatory) == 0

    return {
        "is_valid":          is_valid,
        "missing_mandatory": missing_mandatory,
        "present_optional":  present_optional,
        "missing_optional":  missing_optional,
        "extra_columns":     extra_columns,
    }


def has_column(df: pd.DataFrame, column: str) -> bool:
    """
    Check if a specific column exists in the dataframe.

    Parameters:
        df (pd.DataFrame): The loaded dataset.
        column (str): Column name to check.

    Returns:
        bool: True if column exists, False otherwise.
    """

    return column in df.columns


# =============================================================
# Data Formatting
# =============================================================

def format_bytes(mb: float) -> str:
    """
    Convert a value in megabytes to a human-readable string.
    Automatically scales to GB or TB if large enough.

    Examples:
        format_bytes(512)    → "512.0 MB"
        format_bytes(2048)   → "2.0 GB"
        format_bytes(1100000)→ "1.0 TB"

    Parameters:
        mb (float): Value in megabytes.

    Returns:
        str: Human-readable size string.
    """

    if mb is None or mb != mb:  # handles NaN
        return "N/A"

    if mb >= 1_000_000:
        return f"{mb / 1_000_000:.1f} TB"
    elif mb >= 1_000:
        return f"{mb / 1_000:.2f} GB"
    else:
        return f"{mb:.1f} MB"


def format_number(value: int | float) -> str:
    """
    Format a large number with comma separators.

    Example:
        format_number(123456) → "123,456"

    Parameters:
        value (int | float): The number to format.

    Returns:
        str: Formatted number string.
    """

    if value is None:
        return "N/A"

    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: float, total: float) -> str:
    """
    Calculate and format a percentage string.

    Example:
        format_percentage(25, 100) → "25.0%"

    Parameters:
        value (float): The partial value.
        total (float): The total value.

    Returns:
        str: Percentage string, or "N/A" if total is 0.
    """

    if total == 0:
        return "N/A"

    pct = (value / total) * 100
    return f"{pct:.1f}%"


# =============================================================
# Timestamp Utilities
# =============================================================

def parse_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the Timestamp column into a proper datetime type.
    Adds a 'Hour' column extracted from the Timestamp.

    This function modifies a copy of the dataframe — the
    original is not changed.

    Parameters:
        df (pd.DataFrame): Dataset with a Timestamp column.

    Returns:
        pd.DataFrame: Copy of df with parsed Timestamp + Hour.
    """

    df = df.copy()

    df[COL_TIMESTAMP] = pd.to_datetime(
        df[COL_TIMESTAMP],
        errors="coerce"
    )

    df["Hour"] = df[COL_TIMESTAMP].dt.hour

    return df


def get_peak_hour(df: pd.DataFrame) -> str:
    """
    Find the hour of day with the most log entries.

    Parameters:
        df (pd.DataFrame): Dataset with a parsed Hour column.

    Returns:
        str: Peak hour formatted as "HH:00", or "N/A".
    """

    if "Hour" not in df.columns:
        return "N/A"

    hour_counts = df["Hour"].value_counts()

    if hour_counts.empty:
        return "N/A"

    peak = int(hour_counts.idxmax())

    return f"{peak:02d}:00"


# =============================================================
# File Utilities
# =============================================================

def get_filename(file_path: str) -> str:
    """
    Extract just the filename from a full file path.

    Example:
        get_filename("/home/user/datasets/wifi_logs.csv")
        → "wifi_logs.csv"

    Parameters:
        file_path (str): Full path to a file.

    Returns:
        str: Filename with extension.
    """

    return os.path.basename(file_path)


def get_file_size_kb(file_path: str) -> str:
    """
    Get the size of a file in kilobytes, formatted as a string.

    Example:
        get_file_size_kb("/home/user/datasets/wifi_logs.csv")
        → "42.3 KB"

    Parameters:
        file_path (str): Full path to the file.

    Returns:
        str: File size string, or "N/A" on error.
    """

    try:
        size_bytes = os.path.getsize(file_path)
        size_kb = size_bytes / 1024
        return f"{size_kb:.1f} KB"
    except OSError:
        return "N/A"
