# =============================================================
# config.py — Application Configuration
# Wi-Fi Usage Analyzer
# =============================================================
# All application-wide constants are defined here.
# Import this module in analysis.py, ui.py, and utils.py
# so that all settings stay in one place.
# =============================================================


# -------------------------------------------------------------
# CSV Column Names
# -------------------------------------------------------------
# These are the exact column names expected in the uploaded CSV.
# If the CSV uses different names, the user must rename them.

COL_TIMESTAMP        = "Timestamp"
COL_USERNAME         = "Username"
COL_MAC_ADDRESS      = "MAC_Address"
COL_IP_ADDRESS       = "IP_Address"
COL_DEVICE_NAME      = "Device_Name"
COL_DEVICE_TYPE      = "Device_Type"
COL_SSID             = "SSID"
COL_ACCESS_POINT     = "Access_Point"
COL_WEBSITE          = "Website"
COL_WEBSITE_CATEGORY = "Website_Category"
COL_UPLOAD_MB        = "Upload_MB"
COL_DOWNLOAD_MB      = "Download_MB"
COL_STATUS           = "Status"


# -------------------------------------------------------------
# Mandatory Columns
# -------------------------------------------------------------
# The application requires at least these columns to function.
# If any of these are missing, the file will be rejected.

MANDATORY_COLUMNS = [
    COL_TIMESTAMP,
    COL_USERNAME,
    COL_UPLOAD_MB,
    COL_DOWNLOAD_MB,
]


# -------------------------------------------------------------
# Optional Columns
# -------------------------------------------------------------
# These columns unlock additional features when present.
# Missing optional columns disable their associated pages/cards
# gracefully instead of crashing.

OPTIONAL_COLUMNS = [
    COL_MAC_ADDRESS,
    COL_IP_ADDRESS,
    COL_DEVICE_NAME,
    COL_DEVICE_TYPE,
    COL_SSID,
    COL_ACCESS_POINT,
    COL_WEBSITE,
    COL_WEBSITE_CATEGORY,
    COL_STATUS,
]


# -------------------------------------------------------------
# All Expected Columns (combined)
# -------------------------------------------------------------

ALL_COLUMNS = MANDATORY_COLUMNS + OPTIONAL_COLUMNS


# -------------------------------------------------------------
# Status Column Values
# -------------------------------------------------------------
# These are the expected values inside the Status column.

STATUS_ALLOWED = "Allowed"
STATUS_BLOCKED = "Blocked"


# -------------------------------------------------------------
# Alert Thresholds
# -------------------------------------------------------------
# Rule-based thresholds used in alerts.py / analysis.py.
# Administrators can tune these values for their network.

# Flag a user if their upload in a single session exceeds this (MB)
ALERT_HIGH_UPLOAD_MB = 500

# Flag a user if they are connected to more than this many devices
ALERT_MAX_DEVICES_PER_USER = 3

# Flag a user if they have attempted blocked sites more than this many times
ALERT_BLOCKED_ATTEMPTS = 3

# Flag an access point if it has more than this many users at the same time
ALERT_AP_MAX_USERS = 30


# -------------------------------------------------------------
# UI Colors
# -------------------------------------------------------------
# Centralized color palette used by ui.py.
# Change values here to restyle the entire application.

COLOR_SIDEBAR_BG      = "#1E3A5F"   # Dark navy — sidebar background
COLOR_SIDEBAR_BTN     = "#2C4C72"   # Medium navy — nav button
COLOR_SIDEBAR_HOVER   = "#3B628F"   # Lighter navy — nav button hover
COLOR_SIDEBAR_ACTIVE  = "#4A7AAD"   # Active/selected nav button

COLOR_PAGE_BG         = "#F4F6F8"   # Light grey — main content background
COLOR_CARD_BG         = "#FFFFFF"   # White — stat cards
COLOR_CARD_BORDER     = "#E2E8F0"   # Light border for cards

COLOR_TEXT_PRIMARY    = "#1E293B"   # Near-black — headings
COLOR_TEXT_SECONDARY  = "#64748B"   # Grey — subtext / labels
COLOR_TEXT_SUCCESS    = "#16A34A"   # Green — positive status
COLOR_TEXT_WARNING    = "#D97706"   # Amber — warning status
COLOR_TEXT_DANGER     = "#DC2626"   # Red — alert / danger

COLOR_ACCENT_PRIMARY  = "#1E3A5F"   # Primary accent (matches sidebar)
COLOR_ACCENT_BLUE     = "#3B82F6"   # Bright blue — chart accent
COLOR_ACCENT_GREEN    = "#22C55E"   # Green — upload/download
COLOR_ACCENT_ORANGE   = "#F97316"   # Orange — warnings


# -------------------------------------------------------------
# Font Settings
# -------------------------------------------------------------

FONT_FAMILY   = "Segoe UI"
FONT_HEADING  = (FONT_FAMILY, 24, "bold")
FONT_SUBHEAD  = (FONT_FAMILY, 14, "bold")
FONT_BODY     = (FONT_FAMILY, 11)
FONT_SMALL    = (FONT_FAMILY, 9)
FONT_CARD_VAL = (FONT_FAMILY, 20, "bold")
FONT_CARD_LBL = (FONT_FAMILY, 10)


# -------------------------------------------------------------
# Chart Settings
# -------------------------------------------------------------
# Default figure sizes passed to Matplotlib.

CHART_FIG_WIDE    = (9, 4)    # Wide chart (bar, line)
CHART_FIG_SQUARE  = (5, 4)    # Square chart (pie, donut)
CHART_DPI         = 100       # Screen resolution for charts


# -------------------------------------------------------------
# Application Info
# -------------------------------------------------------------

APP_TITLE   = "Wi-Fi Usage Analyzer"
APP_VERSION = "1.0.0"
APP_AUTHOR  = "Team 1 — DAE Sem 3"
