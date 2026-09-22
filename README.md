# Wi-Fi Usage Analyzer

A Python + Pandas desktop application for analyzing exported Wi-Fi usage logs (CSV files) and generating meaningful insights for network administrators.

> **B.Tech 3rd Semester Project — Data Analysis & Engineering**
> Team 1

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Dataset Format](#dataset-format)
- [Column Compatibility](#column-compatibility)
- [Alert System](#alert-system)
- [Dataset Disclaimer](#dataset-disclaimer)
- [Team](#team)

---

## Overview

Large educational institutions generate thousands of Wi-Fi log entries every day. Manually analyzing these logs is difficult and time-consuming.

The **Wi-Fi Usage Analyzer** automates this task by:

- Accepting exported Wi-Fi usage logs in CSV or Excel format
- Analyzing user behavior, access point utilization, and browsing patterns
- Flagging behavioral anomalies for administrator investigation
- Presenting results through an interactive desktop GUI with charts and tables

> ⚠️ This is **not** a real-time monitoring system, packet sniffer, or intrusion detection system.
> It analyzes **uploaded log files only**.

---

## Features

### Dashboard
- Total users, devices, upload, download, peak usage hour
- Hourly activity bar chart
- Top 10 bandwidth users table
- Download by website category chart

### Users
- Per-user upload / download / total bandwidth / session count
- Sessions by device type (pie chart)
- Unique devices per user

### Access Points
- Per-AP session count, unique users, and total bandwidth
- Sessions per AP (horizontal bar chart)
- Peak simultaneous users per AP with timestamp
- Most overloaded and least utilized AP cards

### Websites
- Browsing category breakdown (pie chart: Education, Streaming, Social Media, etc.)
- Top 15 most visited websites
- All blocked-access attempts with user and timestamp

### Alerts (Rule-Based)
| Alert | Trigger |
|-------|---------|
| High Upload Activity | Single session upload > 500 MB |
| Multiple Devices per User | User connected from ≥ 3 devices |
| Repeated Blocked Site Access | User attempted blocked sites > 3 times |
| Overloaded Access Point | AP peak simultaneous users ≥ 30 |

> Alerts identify unusual patterns for **administrator investigation only**.
> The system does not detect malware, confirm policy violations, or take autonomous action.

### Reports
- Auto-generated network summary report (text format)
- Covers: KPIs, top users, AP stats, alert summary, dataset disclaimer

### Settings
- Loaded dataset info (file, rows, columns, active features)
- Current alert threshold values (configurable in `config.py`)
- Application version and team info

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Data Analysis | Pandas |
| Numerical | NumPy |
| Visualization | Matplotlib |
| GUI | Tkinter (ttk) |
| File Formats | CSV, Excel (.xlsx, .xls) |
| Version Control | Git + GitHub |

No database. No machine learning. No network capture.

---

## Project Structure

```
wifi-usage-analyzer/
│
├── assets/                     # Application assets (icons, etc.)
├── datasets/
│   ├── wifi_logs.csv           # Synthetic demo dataset (934 rows)
│   └── generate_dataset.py     # Script that produced the dataset
│
├── docs/
│   └── ABSTRACT(TEAM-1).pdf
│
├── reports/                    # Output directory for exported reports
│
├── src/
│   ├── main.py                 # Entry point — launches the application
│   ├── ui.py                   # All Tkinter GUI code (7 pages)
│   ├── analysis.py             # All Pandas analysis logic (22 functions)
│   ├── config.py               # Column names, thresholds, colors, fonts
│   └── utils.py                # Shared helper functions (formatting, validation)
│
├── requirements.txt
└── README.md
```

### Module Responsibilities

```
main.py
  └── ui.py                  ← GUI only, no Pandas logic
        └── analysis.py      ← Pandas logic only, no Tkinter
              └── utils.py   ← Pure helpers (formatting, column checks)
              └── config.py  ← All constants (columns, colors, thresholds)
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/AKSHAYPUTTA007/wifi-usage-analyzer.git
cd wifi-usage-analyzer
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### Dependencies

```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
openpyxl>=3.1.0
```

> **Tkinter** is part of the Python standard library and does not need to be installed separately.
> On some Linux systems, run: `sudo apt install python3-tk`

---

## Running the Application

```bash
cd src
python3 main.py
```

The application opens with the **Dashboard** page.
Use the green **Load Dataset** button in the sidebar to upload a CSV or Excel file.

---

## Dataset Format

The application expects a CSV or Excel file with Wi-Fi usage log data.

### Mandatory Columns *(required — file rejected if missing)*

| Column | Description | Example |
|--------|-------------|---------|
| `Timestamp` | Date and time of the session | `2024-11-04 09:30:00` |
| `Username` | User identifier | `cs001` |
| `Upload_MB` | Data uploaded in this session (MB) | `45.2` |
| `Download_MB` | Data downloaded in this session (MB) | `312.7` |

### Optional Columns *(missing columns gracefully disable features)*

| Column | Enables Feature | Example |
|--------|-----------------|---------|
| `MAC_Address` | Device identification | `A1:B2:C3:D4:E5:F6` |
| `IP_Address` | IP-level tracking | `192.168.1.105` |
| `Device_Name` | Device name display | `Dell Inspiron` |
| `Device_Type` | Device type breakdown | `Laptop` / `Smartphone` / `Tablet` |
| `SSID` | Network name | `VIIT-Student` |
| `Access_Point` | AP analysis (entire page) | `AP-LIB-01` |
| `Website` | Top websites table | `youtube.com` |
| `Website_Category` | Category breakdown chart | `Education` / `Streaming` |
| `Status` | Blocked site detection | `Allowed` / `Blocked` |

---

## Column Compatibility

When a file is uploaded, the application automatically checks which columns are present.

- **Missing mandatory columns** → file is rejected with an error message
- **Missing optional columns** → affected features show a yellow notice and are disabled
- **Extra/unknown columns** → silently ignored

This means you can load any compatible Wi-Fi log export — the app adapts to what is available.

---

## Alert System

Alerts are **rule-based** and **informational only**.

| Alert | Rule | Possible Causes |
|-------|------|-----------------|
| High Upload | Single session > 500 MB | Cloud backup, project upload, file sharing, possible data exfiltration |
| Multi-Device | ≥ 3 devices per user | Multiple owned devices, credential sharing |
| Blocked Repeats | > 3 blocked attempts | Policy unawareness, intentional bypass attempt |
| Overloaded AP | ≥ 30 simultaneous users | Peak-hour congestion, poor AP placement |

> The application **never concludes** that malware is present, data was leaked, or a user violated policy.
> All flagged entries require administrator investigation before any action is taken.

Alert thresholds can be adjusted in [`src/config.py`](src/config.py):

```python
ALERT_HIGH_UPLOAD_MB        = 500   # MB per session
ALERT_MAX_DEVICES_PER_USER  = 3     # devices
ALERT_BLOCKED_ATTEMPTS      = 3     # attempts
ALERT_AP_MAX_USERS          = 30    # simultaneous users
```

---

## Dataset Disclaimer

> Synthetic dataset created for educational purposes, inspired by publicly documented enterprise Wi-Fi client log structures.
> No real user data was used.

The included demo dataset (`datasets/wifi_logs.csv`) was generated by `datasets/generate_dataset.py` using a fixed random seed for reproducibility.
It simulates a university Wi-Fi environment with:

- **934 rows** across 6 days (Mon–Sat)
- **100 unique users** across 8 departments
- **12 access points** across campus buildings
- **6 website categories** (Education, Streaming, Social Media, Communication, Cloud Storage, Blocked)
- Embedded anomalies: high upload users, multi-device users, blocked-site repeaters, AP overload scenario

---

## Team

**Team 1 — B.Tech 3rd Semester, Data Analysis & Engineering**

| Member | Responsibility |
|--------|---------------|
| Akshay | UI development + project integration |
| *(Team member 2)* | Data analysis (`analysis.py`) |
| *(Team member 3)* | Dataset generation + documentation |
| *(Team member 4)* | Configuration + testing |
