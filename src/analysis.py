# =============================================================
# analysis.py — All Pandas Analysis Logic
# Wi-Fi Usage Analyzer
# =============================================================
# This module contains ONLY data analysis functions.
# No Tkinter. No charts. No UI.
#
# Every function:
#   - Accepts a pandas DataFrame as its first argument.
#   - Returns a DataFrame, dict, or scalar value.
#   - Handles missing optional columns gracefully.
#   - Is safe to call independently (no shared state).
#
# Import structure:
#   ui.py  →  analysis.py  →  config.py / utils.py
# =============================================================

import pandas as pd
from utils import has_column, parse_timestamps, get_peak_hour
from config import (
    COL_TIMESTAMP,
    COL_USERNAME,
    COL_MAC_ADDRESS,
    COL_DEVICE_NAME,
    COL_DEVICE_TYPE,
    COL_ACCESS_POINT,
    COL_WEBSITE,
    COL_WEBSITE_CATEGORY,
    COL_UPLOAD_MB,
    COL_DOWNLOAD_MB,
    COL_STATUS,
    STATUS_BLOCKED,
    ALERT_HIGH_UPLOAD_MB,
    ALERT_MAX_DEVICES_PER_USER,
    ALERT_BLOCKED_ATTEMPTS,
    ALERT_AP_MAX_USERS,
)


# =============================================================
# SECTION 1 — Dashboard Statistics
# =============================================================

def get_total_users(df: pd.DataFrame) -> int:
    """
    Count the number of unique users in the dataset.

    Returns:
        int: Number of unique usernames.
    """
    return df[COL_USERNAME].nunique()


def get_total_devices(df: pd.DataFrame) -> int:
    """
    Count the number of unique devices (by MAC Address).
    Falls back to counting unique device names if MAC is absent.

    Returns:
        int: Number of unique devices, or 0 if no device column exists.
    """
    if has_column(df, COL_MAC_ADDRESS):
        return df[COL_MAC_ADDRESS].nunique()
    elif has_column(df, COL_DEVICE_NAME):
        return df[COL_DEVICE_NAME].nunique()
    return 0


def get_total_upload(df: pd.DataFrame) -> float:
    """
    Sum all Upload_MB values.

    Returns:
        float: Total upload in MB.
    """
    return round(df[COL_UPLOAD_MB].sum(), 2)


def get_total_download(df: pd.DataFrame) -> float:
    """
    Sum all Download_MB values.

    Returns:
        float: Total download in MB.
    """
    return round(df[COL_DOWNLOAD_MB].sum(), 2)


def get_peak_usage_hour(df: pd.DataFrame) -> str:
    """
    Find the hour of day with the highest number of log entries.

    Returns:
        str: Peak hour as "HH:00", e.g. "12:00". Returns "N/A" if
             Timestamp column cannot be parsed.
    """
    if not has_column(df, COL_TIMESTAMP):
        return "N/A"

    df_parsed = parse_timestamps(df)
    return get_peak_hour(df_parsed)


def get_dashboard_summary(df: pd.DataFrame) -> dict:
    """
    Compute all top-level KPI values shown on the Dashboard cards.

    Returns:
        dict with keys:
            total_users     (int)
            total_devices   (int)
            total_upload_mb (float)
            total_download_mb (float)
            peak_hour       (str)
    """
    return {
        "total_users":       get_total_users(df),
        "total_devices":     get_total_devices(df),
        "total_upload_mb":   get_total_upload(df),
        "total_download_mb": get_total_download(df),
        "peak_hour":         get_peak_usage_hour(df),
    }


def get_top_bandwidth_users(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Return the top N users by total data usage (upload + download).

    Parameters:
        df (pd.DataFrame): Dataset.
        n  (int): Number of top users to return. Default is 10.

    Returns:
        pd.DataFrame with columns:
            Username, Upload_MB, Download_MB, Total_MB
        Sorted descending by Total_MB.
    """
    grouped = df.groupby(COL_USERNAME, as_index=False).agg(
        Upload_MB=(COL_UPLOAD_MB, "sum"),
        Download_MB=(COL_DOWNLOAD_MB, "sum"),
    )

    grouped["Total_MB"] = grouped["Upload_MB"] + grouped["Download_MB"]
    grouped = grouped.sort_values("Total_MB", ascending=False)
    grouped = grouped.head(n).reset_index(drop=True)

    # Round for cleaner display
    grouped["Upload_MB"]   = grouped["Upload_MB"].round(2)
    grouped["Download_MB"] = grouped["Download_MB"].round(2)
    grouped["Total_MB"]    = grouped["Total_MB"].round(2)

    return grouped


def get_top_website_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return website category usage, sorted by total download (most consumed).

    Requires: Website_Category, Download_MB columns.

    Returns:
        pd.DataFrame with columns:
            Website_Category, Sessions, Download_MB, Upload_MB
        Returns empty DataFrame if Website_Category is missing.
    """
    if not has_column(df, COL_WEBSITE_CATEGORY):
        return pd.DataFrame()

    grouped = df.groupby(COL_WEBSITE_CATEGORY, as_index=False).agg(
        Sessions=(COL_USERNAME, "count"),
        Download_MB=(COL_DOWNLOAD_MB, "sum"),
        Upload_MB=(COL_UPLOAD_MB, "sum"),
    )

    grouped = grouped.sort_values("Download_MB", ascending=False)
    grouped["Download_MB"] = grouped["Download_MB"].round(2)
    grouped["Upload_MB"]   = grouped["Upload_MB"].round(2)

    return grouped.reset_index(drop=True)


def get_hourly_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count the number of log entries per hour of day.
    Used for the Dashboard activity bar chart.

    Returns:
        pd.DataFrame with columns:
            Hour (int 0–23), Sessions (int)
        All 24 hours are present (0 if no activity).
    """
    if not has_column(df, COL_TIMESTAMP):
        return pd.DataFrame()

    df_parsed = parse_timestamps(df)
    hourly = df_parsed.groupby("Hour", as_index=False).agg(
        Sessions=(COL_USERNAME, "count")
    )

    # Ensure all 24 hours exist even if some have 0 sessions
    all_hours = pd.DataFrame({"Hour": range(24)})
    hourly = all_hours.merge(hourly, on="Hour", how="left").fillna(0)
    hourly["Sessions"] = hourly["Sessions"].astype(int)

    return hourly


# =============================================================
# SECTION 2 — User Analysis
# =============================================================

def get_user_bandwidth_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-user summary of upload, download, and total bandwidth.

    Returns:
        pd.DataFrame with columns:
            Username, Upload_MB, Download_MB, Total_MB, Sessions
        Sorted descending by Total_MB.
    """
    grouped = df.groupby(COL_USERNAME, as_index=False).agg(
        Upload_MB=(COL_UPLOAD_MB, "sum"),
        Download_MB=(COL_DOWNLOAD_MB, "sum"),
        Sessions=(COL_UPLOAD_MB, "count"),
    )

    grouped["Total_MB"] = grouped["Upload_MB"] + grouped["Download_MB"]
    grouped = grouped.sort_values("Total_MB", ascending=False)
    grouped["Upload_MB"]   = grouped["Upload_MB"].round(2)
    grouped["Download_MB"] = grouped["Download_MB"].round(2)
    grouped["Total_MB"]    = grouped["Total_MB"].round(2)

    return grouped.reset_index(drop=True)


def get_user_device_count(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count the number of unique devices per user.

    Requires: MAC_Address column (falls back to Device_Name).

    Returns:
        pd.DataFrame with columns:
            Username, Device_Count
        Sorted descending by Device_Count.
        Returns empty DataFrame if no device identifier column exists.
    """
    if has_column(df, COL_MAC_ADDRESS):
        device_col = COL_MAC_ADDRESS
    elif has_column(df, COL_DEVICE_NAME):
        device_col = COL_DEVICE_NAME
    else:
        return pd.DataFrame()

    grouped = df.groupby(COL_USERNAME, as_index=False).agg(
        Device_Count=(device_col, "nunique")
    )

    return grouped.sort_values(
        "Device_Count", ascending=False
    ).reset_index(drop=True)


def get_user_device_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count usage sessions broken down by device type.

    Requires: Device_Type column.

    Returns:
        pd.DataFrame with columns:
            Device_Type, Sessions
        Returns empty DataFrame if Device_Type is missing.
    """
    if not has_column(df, COL_DEVICE_TYPE):
        return pd.DataFrame()

    grouped = df.groupby(COL_DEVICE_TYPE, as_index=False).agg(
        Sessions=(COL_USERNAME, "count")
    )

    return grouped.sort_values(
        "Sessions", ascending=False
    ).reset_index(drop=True)


def get_user_detail(df: pd.DataFrame, username: str) -> dict:
    """
    Get a detailed summary for a specific user.

    Parameters:
        df       (pd.DataFrame): Full dataset.
        username (str): The username to look up.

    Returns:
        dict with keys:
            username, total_upload_mb, total_download_mb,
            total_mb, sessions, devices (list), top_websites (list)
        Returns an empty dict if user is not found.
    """
    user_df = df[df[COL_USERNAME] == username]

    if user_df.empty:
        return {}

    devices = []
    if has_column(df, COL_MAC_ADDRESS):
        devices = user_df[COL_MAC_ADDRESS].unique().tolist()

    top_websites = []
    if has_column(df, COL_WEBSITE):
        top_websites = (
            user_df[COL_WEBSITE]
            .value_counts()
            .head(5)
            .index.tolist()
        )

    return {
        "username":         username,
        "total_upload_mb":  round(user_df[COL_UPLOAD_MB].sum(), 2),
        "total_download_mb": round(user_df[COL_DOWNLOAD_MB].sum(), 2),
        "total_mb":         round(
            user_df[COL_UPLOAD_MB].sum() + user_df[COL_DOWNLOAD_MB].sum(), 2
        ),
        "sessions":         len(user_df),
        "devices":          devices,
        "top_websites":     top_websites,
    }


# =============================================================
# SECTION 3 — Access Point Analysis
# =============================================================

def get_ap_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-AP summary: unique users, total sessions, total bandwidth.

    Requires: Access_Point column.

    Returns:
        pd.DataFrame with columns:
            Access_Point, Unique_Users, Sessions, Upload_MB, Download_MB, Total_MB
        Sorted descending by Sessions.
        Returns empty DataFrame if Access_Point is missing.
    """
    if not has_column(df, COL_ACCESS_POINT):
        return pd.DataFrame()

    grouped = df.groupby(COL_ACCESS_POINT, as_index=False).agg(
        Unique_Users=(COL_USERNAME, "nunique"),
        Sessions=(COL_USERNAME, "count"),
        Upload_MB=(COL_UPLOAD_MB, "sum"),
        Download_MB=(COL_DOWNLOAD_MB, "sum"),
    )

    grouped["Total_MB"] = grouped["Upload_MB"] + grouped["Download_MB"]
    grouped = grouped.sort_values("Sessions", ascending=False)
    grouped["Upload_MB"]   = grouped["Upload_MB"].round(2)
    grouped["Download_MB"] = grouped["Download_MB"].round(2)
    grouped["Total_MB"]    = grouped["Total_MB"].round(2)

    return grouped.reset_index(drop=True)


def get_ap_peak_users(df: pd.DataFrame) -> pd.DataFrame:
    """
    Find the maximum number of simultaneous users at each AP.

    Simultaneous = same Timestamp value (minute-level granularity).

    Requires: Access_Point, Timestamp columns.

    Returns:
        pd.DataFrame with columns:
            Access_Point, Peak_Users, Peak_Timestamp
        Sorted descending by Peak_Users.
        Returns empty DataFrame if required columns are missing.
    """
    if not has_column(df, COL_ACCESS_POINT) or not has_column(df, COL_TIMESTAMP):
        return pd.DataFrame()

    df_parsed = parse_timestamps(df)

    # Round timestamps to the nearest minute for grouping
    df_parsed = df_parsed.copy()
    df_parsed["Minute"] = df_parsed[COL_TIMESTAMP].dt.floor("min")

    # Count distinct users per (AP, Minute)
    concurrent = df_parsed.groupby(
        [COL_ACCESS_POINT, "Minute"], as_index=False
    ).agg(Users=(COL_USERNAME, "nunique"))

    # Find the peak minute for each AP
    peak = concurrent.loc[
        concurrent.groupby(COL_ACCESS_POINT)["Users"].idxmax()
    ].copy()

    peak = peak.rename(columns={
        "Users":  "Peak_Users",
        "Minute": "Peak_Timestamp"
    })

    peak["Peak_Timestamp"] = peak["Peak_Timestamp"].astype(str)
    peak = peak.sort_values("Peak_Users", ascending=False)

    return peak[[COL_ACCESS_POINT, "Peak_Users", "Peak_Timestamp"]].reset_index(drop=True)


def get_ap_utilization_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count total sessions per AP per hour across the dataset.
    Used to draw an AP utilization line/bar chart over time.

    Requires: Access_Point, Timestamp columns.

    Returns:
        pd.DataFrame with columns:
            Hour (int), Access_Point (str), Sessions (int)
        Returns empty DataFrame if required columns are missing.
    """
    if not has_column(df, COL_ACCESS_POINT) or not has_column(df, COL_TIMESTAMP):
        return pd.DataFrame()

    df_parsed = parse_timestamps(df)

    grouped = df_parsed.groupby(
        ["Hour", COL_ACCESS_POINT], as_index=False
    ).agg(Sessions=(COL_USERNAME, "count"))

    return grouped.sort_values(["Hour", COL_ACCESS_POINT]).reset_index(drop=True)


def get_most_overloaded_ap(df: pd.DataFrame) -> str:
    """
    Return the name of the single most overloaded AP
    (the one with the highest peak simultaneous users).

    Returns:
        str: AP name, or "N/A" if data is unavailable.
    """
    peak_df = get_ap_peak_users(df)

    if peak_df.empty:
        return "N/A"

    return peak_df.iloc[0][COL_ACCESS_POINT]


def get_least_utilized_ap(df: pd.DataFrame) -> str:
    """
    Return the name of the AP with the fewest total sessions.

    Returns:
        str: AP name, or "N/A" if data is unavailable.
    """
    summary = get_ap_summary(df)

    if summary.empty:
        return "N/A"

    return summary.iloc[-1][COL_ACCESS_POINT]


# =============================================================
# SECTION 4 — Website Analysis
# =============================================================

def get_top_websites(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Return the N most visited websites by session count.

    Requires: Website column.

    Parameters:
        n (int): Number of websites to return. Default is 10.

    Returns:
        pd.DataFrame with columns:
            Website, Sessions, Download_MB
        Sorted descending by Sessions.
        Returns empty DataFrame if Website is missing.
    """
    if not has_column(df, COL_WEBSITE):
        return pd.DataFrame()

    grouped = df.groupby(COL_WEBSITE, as_index=False).agg(
        Sessions=(COL_USERNAME, "count"),
        Download_MB=(COL_DOWNLOAD_MB, "sum"),
    )

    grouped["Download_MB"] = grouped["Download_MB"].round(2)
    grouped = grouped.sort_values("Sessions", ascending=False)

    return grouped.head(n).reset_index(drop=True)


def get_category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return session count and bandwidth per website category.
    Used for the category pie/bar chart.

    Requires: Website_Category column.

    Returns:
        pd.DataFrame with columns:
            Website_Category, Sessions, Download_MB, Upload_MB
        Sorted descending by Sessions.
        Returns empty DataFrame if Website_Category is missing.
    """
    if not has_column(df, COL_WEBSITE_CATEGORY):
        return pd.DataFrame()

    grouped = df.groupby(COL_WEBSITE_CATEGORY, as_index=False).agg(
        Sessions=(COL_USERNAME, "count"),
        Download_MB=(COL_DOWNLOAD_MB, "sum"),
        Upload_MB=(COL_UPLOAD_MB, "sum"),
    )

    grouped["Download_MB"] = grouped["Download_MB"].round(2)
    grouped["Upload_MB"]   = grouped["Upload_MB"].round(2)

    return grouped.sort_values(
        "Sessions", ascending=False
    ).reset_index(drop=True)


def get_blocked_sites(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return all sessions where Status = Blocked.

    Requires: Status column.

    Returns:
        pd.DataFrame of blocked rows, sorted by Username.
        Returns empty DataFrame if Status column is missing.
    """
    if not has_column(df, COL_STATUS):
        return pd.DataFrame()

    blocked = df[df[COL_STATUS] == STATUS_BLOCKED].copy()

    return blocked.sort_values(COL_USERNAME).reset_index(drop=True)


# =============================================================
# SECTION 5 — Alerts
# =============================================================

def alert_high_upload(df: pd.DataFrame) -> pd.DataFrame:
    """
    ALERT: Unusually High Upload Activity.

    Flags users whose total Upload_MB across the dataset
    exceeds ALERT_HIGH_UPLOAD_MB (defined in config.py).

    Administrator action:
        Investigate possible cloud backup, large project uploads,
        or potential data exfiltration.

    Returns:
        pd.DataFrame with columns:
            Username, Total_Upload_MB, Threshold_MB
        Sorted descending by Total_Upload_MB.
        Empty DataFrame if no violations found.
    """
    # Flag individual log entries (sessions) where upload > threshold.
    # A single anomalous upload session is more meaningful than a total.
    flagged = df[df[COL_UPLOAD_MB] > ALERT_HIGH_UPLOAD_MB][
        [COL_USERNAME, COL_UPLOAD_MB]
    ].copy()

    flagged = flagged.rename(columns={COL_UPLOAD_MB: "Upload_MB"})
    flagged["Upload_MB"]   = flagged["Upload_MB"].round(2)
    flagged["Threshold_MB"] = ALERT_HIGH_UPLOAD_MB
    flagged = flagged.sort_values("Upload_MB", ascending=False)

    return flagged.reset_index(drop=True)


def alert_multiple_devices(df: pd.DataFrame) -> pd.DataFrame:
    """
    ALERT: Multiple Devices Per User.

    Flags users who are connected from more than
    ALERT_MAX_DEVICES_PER_USER unique devices (defined in config.py).

    Requires: MAC_Address column (falls back to Device_Name).

    Administrator action:
        Verify whether the user legitimately owns multiple devices
        or if credentials are being shared.

    Returns:
        pd.DataFrame with columns:
            Username, Device_Count, Max_Allowed
        Sorted descending by Device_Count.
        Empty DataFrame if no violations found or column missing.
    """
    if has_column(df, COL_MAC_ADDRESS):
        device_col = COL_MAC_ADDRESS
    elif has_column(df, COL_DEVICE_NAME):
        device_col = COL_DEVICE_NAME
    else:
        return pd.DataFrame()

    device_counts = df.groupby(COL_USERNAME, as_index=False).agg(
        Device_Count=(device_col, "nunique")
    )

    flagged = device_counts[
        device_counts["Device_Count"] >= ALERT_MAX_DEVICES_PER_USER
    ].copy()

    flagged["Max_Allowed"] = ALERT_MAX_DEVICES_PER_USER
    flagged = flagged.sort_values("Device_Count", ascending=False)

    return flagged.reset_index(drop=True)


def alert_blocked_repeat(df: pd.DataFrame) -> pd.DataFrame:
    """
    ALERT: Repeated Blocked Website Access.

    Flags users who have been blocked more than
    ALERT_BLOCKED_ATTEMPTS times (defined in config.py).

    Requires: Status column.

    Administrator action:
        Speak with the user about acceptable use policy.
        Investigate if access attempts suggest policy violation.

    Returns:
        pd.DataFrame with columns:
            Username, Blocked_Attempts, Threshold
        Sorted descending by Blocked_Attempts.
        Empty DataFrame if no violations found or column missing.
    """
    if not has_column(df, COL_STATUS):
        return pd.DataFrame()

    blocked_df = df[df[COL_STATUS] == STATUS_BLOCKED]

    if blocked_df.empty:
        return pd.DataFrame()

    attempt_counts = blocked_df.groupby(
        COL_USERNAME, as_index=False
    ).agg(Blocked_Attempts=(COL_STATUS, "count"))

    flagged = attempt_counts[
        attempt_counts["Blocked_Attempts"] > ALERT_BLOCKED_ATTEMPTS
    ].copy()

    flagged["Threshold"] = ALERT_BLOCKED_ATTEMPTS
    flagged = flagged.sort_values("Blocked_Attempts", ascending=False)

    return flagged.reset_index(drop=True)


def alert_overloaded_ap(df: pd.DataFrame) -> pd.DataFrame:
    """
    ALERT: Overloaded Access Point.

    Flags access points where the peak simultaneous user count
    exceeds ALERT_AP_MAX_USERS (defined in config.py).

    Requires: Access_Point, Timestamp columns.

    Administrator action:
        Consider load balancing, adding more APs, or limiting
        connections per AP during peak hours.

    Returns:
        pd.DataFrame with columns:
            Access_Point, Peak_Users, Peak_Timestamp, Max_Allowed
        Sorted descending by Peak_Users.
        Empty DataFrame if no violations found or columns missing.
    """
    peak_df = get_ap_peak_users(df)

    if peak_df.empty:
        return pd.DataFrame()

    flagged = peak_df[
        peak_df["Peak_Users"] >= ALERT_AP_MAX_USERS
    ].copy()

    flagged["Max_Allowed"] = ALERT_AP_MAX_USERS
    flagged = flagged.sort_values("Peak_Users", ascending=False)

    return flagged.reset_index(drop=True)


def get_all_alerts(df: pd.DataFrame) -> dict:
    """
    Run all four alert checks and return results together.
    Used by the Alerts page to display all alerts at once.

    Returns:
        dict with keys:
            high_upload     (pd.DataFrame)
            multi_device    (pd.DataFrame)
            blocked_repeat  (pd.DataFrame)
            overloaded_ap   (pd.DataFrame)
            total_alerts    (int) — total flagged entries across all checks
    """
    high_upload    = alert_high_upload(df)
    multi_device   = alert_multiple_devices(df)
    blocked_repeat = alert_blocked_repeat(df)
    overloaded_ap  = alert_overloaded_ap(df)

    total_alerts = (
        len(high_upload) +
        len(multi_device) +
        len(blocked_repeat) +
        len(overloaded_ap)
    )

    return {
        "high_upload":    high_upload,
        "multi_device":   multi_device,
        "blocked_repeat": blocked_repeat,
        "overloaded_ap":  overloaded_ap,
        "total_alerts":   total_alerts,
    }
