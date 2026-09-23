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
# Alert Thresholds (Defaults)
# -------------------------------------------------------------
# Baseline rule-based thresholds used in analysis.py.
# Administrators can tune these interactively in the UI or save
# persistent preferences to USER_SETTINGS_FILE.

DEFAULT_ALERT_HIGH_UPLOAD_MB       = 500
DEFAULT_ALERT_MAX_DEVICES_PER_USER = 3
DEFAULT_ALERT_BLOCKED_ATTEMPTS     = 3
DEFAULT_ALERT_AP_MAX_USERS         = 30

# Backwards-compatible aliases
ALERT_HIGH_UPLOAD_MB       = DEFAULT_ALERT_HIGH_UPLOAD_MB
ALERT_MAX_DEVICES_PER_USER = DEFAULT_ALERT_MAX_DEVICES_PER_USER
ALERT_BLOCKED_ATTEMPTS     = DEFAULT_ALERT_BLOCKED_ATTEMPTS
ALERT_AP_MAX_USERS         = DEFAULT_ALERT_AP_MAX_USERS

# Persistence file for user custom thresholds
USER_SETTINGS_FILE = "user_settings.json"


# -------------------------------------------------------------
# UI Colors — Professional Dark Cyber / NOC Palette
# -------------------------------------------------------------
# Deep obsidian, slate-900 surfaces, crisp white typography,
# and high-contrast glowing neon accents.

COLOR_PAGE_BG         = "#0B0F19"   # Obsidian dark — main content background
COLOR_SIDEBAR_BG      = "#0A0D18"   # Deepest slate dark — sidebar background
COLOR_SIDEBAR_BTN     = "#131C2E"   # Sidebar nav button background
COLOR_SIDEBAR_HOVER   = "#1E2C48"   # Nav button hover
COLOR_SIDEBAR_ACTIVE  = "#2563EB"   # Electric Cobalt Blue — active nav item

COLOR_CARD_BG         = "#111827"   # Dark card surface (Zinc/Slate-900)
COLOR_CARD_BORDER     = "#1F293D"   # Subtle card outline border
COLOR_CARD_INNER      = "#0F172A"   # Recessed container / chart background
COLOR_INPUT_BG        = "#0B1120"   # Recessed input / spinbox background
COLOR_INPUT_BORDER    = "#334155"   # Input field border

COLOR_TEXT_PRIMARY    = "#F8FAFC"   # Bright crisp white — headings & key values
COLOR_TEXT_SECONDARY  = "#94A3B8"   # Slate muted gray — labels & subtext
COLOR_TEXT_MUTED      = "#64748B"   # Dim gray — hints & notes
COLOR_TEXT_SUCCESS    = "#34D399"   # Emerald green status
COLOR_TEXT_WARNING    = "#FBBF24"   # Amber yellow status
COLOR_TEXT_DANGER     = "#F87171"   # Coral red alert

# Access Point Capacity Status Colors
COLOR_STATUS_NORMAL   = "#10B981"   # Emerald green (< 75% load)
COLOR_STATUS_WARNING  = "#F59E0B"   # Amber yellow (75% - 99% load)
COLOR_STATUS_OVERLOAD = "#EF4444"   # Crimson red (>= 100% load)

COLOR_ACCENT_PRIMARY  = "#2563EB"   # Cobalt Blue
COLOR_ACCENT_HOVER    = "#1D4ED8"   # Darker Cobalt for button active/hover
COLOR_ACCENT_BLUE     = "#38BDF8"   # Neon Cyan / Sky Blue
COLOR_ACCENT_GREEN    = "#34D399"   # Emerald Mint
COLOR_ACCENT_ORANGE   = "#FB923C"   # Vibrant Orange
COLOR_ACCENT_PURPLE   = "#A78BFA"   # Purple Accent


# -------------------------------------------------------------
# Font Settings
# -------------------------------------------------------------

FONT_FAMILY   = "Segoe UI"
FONT_HEADING  = (FONT_FAMILY, 22, "bold")
FONT_SUBHEAD  = (FONT_FAMILY, 13, "bold")
FONT_BODY     = (FONT_FAMILY, 10)
FONT_SMALL    = (FONT_FAMILY, 9)
FONT_CARD_VAL = (FONT_FAMILY, 20, "bold")
FONT_CARD_LBL = (FONT_FAMILY, 9)


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
