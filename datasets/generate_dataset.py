# =============================================================
# generate_dataset.py — Synthetic Dataset Generator
# Wi-Fi Usage Analyzer
# =============================================================
# Generates a realistic university Wi-Fi usage log CSV.
#
# Dataset disclaimer:
#   Synthetic dataset created for educational purposes, inspired
#   by publicly documented enterprise Wi-Fi client log structures.
#   No real user data was used.
#
# Run this script once from the datasets/ directory:
#   python generate_dataset.py
# =============================================================

import random
import csv
import os
from datetime import datetime, timedelta

random.seed(42)  # Fixed seed for reproducibility

# =============================================================
# Output File
# =============================================================

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "wifi_logs.csv")

# =============================================================
# University Environment Data
# =============================================================

# ---------------------------
# Students (~100 usernames)
# ---------------------------
FIRST_NAMES = [
    "Akshay", "Priya", "Rahul", "Sneha", "Arjun", "Divya", "Kiran",
    "Meera", "Rohan", "Anjali", "Vikram", "Pooja", "Suresh", "Kavya",
    "Nikhil", "Lakshmi", "Aditya", "Swathi", "Harish", "Nandini",
    "Sanjay", "Deepa", "Manoj", "Asha", "Ravi", "Suma", "Krishna",
    "Rekha", "Venkat", "Padma", "Ganesh", "Usha", "Praveen", "Geetha",
    "Naveen", "Sarala", "Rajesh", "Hema", "Sunil", "Vani", "Mohan",
    "Leela", "Dinesh", "Kamala", "Anand", "Shoba", "Kumar", "Revathi",
    "Vinay", "Malathi"
]

DEPARTMENTS = ["CS", "EC", "ME", "CE", "IT", "EE", "BT", "CH"]

# Generate 100 unique usernames like cs001, ec002, etc.
STUDENTS = []
for i, name in enumerate(FIRST_NAMES):
    dept = random.choice(DEPARTMENTS).lower()
    num = str(i + 1).zfill(3)
    username = f"{dept}{num}"
    STUDENTS.append(username)

# Extend to 100 if needed
while len(STUDENTS) < 100:
    dept = random.choice(DEPARTMENTS).lower()
    num = str(len(STUDENTS) + 1).zfill(3)
    STUDENTS.append(f"{dept}{num}")

# ---------------------------
# Devices
# ---------------------------
DEVICE_TYPES = ["Laptop", "Smartphone", "Tablet"]

LAPTOP_NAMES  = ["Dell Inspiron", "HP Pavilion", "Lenovo IdeaPad", "Asus VivoBook", "Acer Aspire"]
PHONE_NAMES   = ["Samsung Galaxy A52", "Redmi Note 12", "OnePlus Nord", "Realme 10 Pro", "iPhone 13"]
TABLET_NAMES  = ["iPad Air", "Samsung Tab A7", "Lenovo Tab P11"]

# ---------------------------
# Access Points (university buildings)
# ---------------------------
ACCESS_POINTS = [
    "AP-LIB-01",   # Library
    "AP-LIB-02",
    "AP-CSE-01",   # CSE Block
    "AP-CSE-02",
    "AP-ECE-01",   # ECE Block
    "AP-MECH-01",  # Mechanical Block
    "AP-CAFE-01",  # Cafeteria
    "AP-ADMIN-01", # Admin Block
    "AP-HOSTEL-01",# Hostel
    "AP-HOSTEL-02",
    "AP-GYM-01",   # Gym
    "AP-SEMHALL-01"# Seminar Hall
]

SSIDS = ["VIIT-Student", "VIIT-Faculty", "VIIT-Guest"]

# ---------------------------
# Websites and Categories
# ---------------------------
WEBSITES = {
    "Education": [
        "nptel.ac.in", "coursera.org", "classroom.google.com",
        "ktu.edu.in", "moodle.viit.ac.in", "geeksforgeeks.org",
        "w3schools.com", "stackoverflow.com", "github.com"
    ],
    "Streaming": [
        "youtube.com", "hotstar.com", "netflix.com",
        "primevideo.com", "spotify.com", "jiocinema.com"
    ],
    "Social Media": [
        "instagram.com", "twitter.com", "facebook.com",
        "linkedin.com", "snapchat.com", "reddit.com"
    ],
    "Cloud Storage": [
        "drive.google.com", "dropbox.com", "onedrive.live.com",
        "wetransfer.com"
    ],
    "Communication": [
        "mail.google.com", "outlook.com", "teams.microsoft.com",
        "zoom.us", "meet.google.com", "whatsapp.com"
    ],
    "Blocked": [
        "torrent-galaxy.to", "1337x.to", "piratebay.org",
        "bet365.com", "pokerstar.com", "vpngate.net",
        "pornhub.com", "fmovies.io"
    ]
}

# ---------------------------
# Timestamp Range (one full week, Mon–Sat, university hours)
# ---------------------------
START_DATE = datetime(2024, 11, 4, 8, 0, 0)   # Monday 08:00
END_DATE   = datetime(2024, 11, 9, 22, 0, 0)  # Saturday 22:00

# =============================================================
# Helper Functions
# =============================================================

def random_mac():
    """Generate a random MAC address."""
    parts = [f"{random.randint(0x00, 0xFF):02X}" for _ in range(6)]
    return ":".join(parts)


def random_ip():
    """Generate a random private IP in 192.168.x.x range."""
    return f"192.168.{random.randint(1, 10)}.{random.randint(2, 254)}"


def random_timestamp():
    """Return a random datetime within the week, biased toward peak hours."""
    # Pick a random day offset (0–5)
    day_offset = random.randint(0, 5)
    # Peak hours: 9–13 and 14–18 (class hours)
    # Off-peak: 8–9, 18–22 (hostel/evening)
    hour_weights = [
        (8,  9,  0.04),
        (9,  12, 0.25),
        (12, 14, 0.10),
        (14, 17, 0.25),
        (17, 19, 0.12),
        (19, 22, 0.24),
    ]
    r = random.random()
    cumulative = 0
    chosen_hour = 9
    for h_start, h_end, weight in hour_weights:
        cumulative += weight
        if r <= cumulative:
            chosen_hour = random.randint(h_start, h_end - 1)
            break

    minute  = random.randint(0, 59)
    second  = random.randint(0, 59)
    ts = START_DATE + timedelta(days=day_offset)
    ts = ts.replace(hour=chosen_hour, minute=minute, second=second)
    return ts


def get_device_name(device_type):
    """Return a realistic device name for the given device type."""
    if device_type == "Laptop":
        return random.choice(LAPTOP_NAMES)
    elif device_type == "Smartphone":
        return random.choice(PHONE_NAMES)
    else:
        return random.choice(TABLET_NAMES)


# =============================================================
# Build Student Profiles
# =============================================================
# Each student gets:
#   - 1 to 3 devices (username → list of (mac, ip, device_name, device_type))
#   - A preferred AP zone
#   - A flag for anomaly type (normal / high_upload / multi_device / blocked_repeater)

student_profiles = {}

for username in STUDENTS:
    # Most students have 1 device; some have 2–3
    num_devices_weight = random.random()
    if num_devices_weight < 0.65:
        num_devices = 1
    elif num_devices_weight < 0.85:
        num_devices = 2
    else:
        num_devices = 3

    devices = []
    used_macs = set()
    for _ in range(num_devices):
        mac = random_mac()
        while mac in used_macs:
            mac = random_mac()
        used_macs.add(mac)

        device_type = random.choice(DEVICE_TYPES)
        device_name = get_device_name(device_type)
        ip = random_ip()
        devices.append({
            "mac":         mac,
            "ip":          ip,
            "device_name": device_name,
            "device_type": device_type,
        })

    preferred_ap   = random.choice(ACCESS_POINTS)
    preferred_ssid = random.choice(SSIDS)

    # Assign anomaly role to ~15% of students
    anomaly_roll = random.random()
    if anomaly_roll < 0.08:
        anomaly = "high_upload"       # Will generate >500 MB upload entries
    elif anomaly_roll < 0.13:
        anomaly = "blocked_repeater"  # Will repeatedly access blocked sites
    else:
        anomaly = "normal"

    student_profiles[username] = {
        "devices":        devices,
        "preferred_ap":   preferred_ap,
        "preferred_ssid": preferred_ssid,
        "anomaly":        anomaly,
    }

# =============================================================
# Generate Log Rows
# =============================================================

rows = []

for username, profile in student_profiles.items():
    anomaly = profile["anomaly"]

    # Each student generates 6–12 log entries
    num_entries = random.randint(6, 12)

    for _ in range(num_entries):

        # Pick one of the student's devices
        device = random.choice(profile["devices"])

        # AP: mostly preferred, occasionally roams
        if random.random() < 0.75:
            ap = profile["preferred_ap"]
        else:
            ap = random.choice(ACCESS_POINTS)

        ssid = profile["preferred_ssid"]

        # Website and category
        if anomaly == "blocked_repeater" and random.random() < 0.55:
            category = "Blocked"
        else:
            category = random.choices(
                population=list(WEBSITES.keys()),
                weights=[30, 20, 20, 10, 15, 5],
                k=1
            )[0]

        website = random.choice(WEBSITES[category])
        status  = "Blocked" if category == "Blocked" else "Allowed"

        # Upload / Download
        if anomaly == "high_upload" and random.random() < 0.4:
            upload_mb   = round(random.uniform(600, 2500), 2)  # Abnormally high
            download_mb = round(random.uniform(10, 200), 2)
        else:
            upload_mb   = round(random.uniform(0.5, 150), 2)
            download_mb = round(random.uniform(5, 800), 2)

        # Timestamp
        ts = random_timestamp()

        rows.append({
            "Timestamp":        ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Username":         username,
            "MAC_Address":      device["mac"],
            "IP_Address":       device["ip"],
            "Device_Name":      device["device_name"],
            "Device_Type":      device["device_type"],
            "SSID":             ssid,
            "Access_Point":     ap,
            "Website":          website,
            "Website_Category": category,
            "Upload_MB":        upload_mb,
            "Download_MB":      download_mb,
            "Status":           status,
        })

# ------------------------------------------------------------------
# Inject overloaded AP scenario
# ------------------------------------------------------------------
# Force 35 simultaneous entries on AP-CAFE-01 at lunch (12:30) on Day 2
# so the overloaded AP alert fires reliably during demo.

overload_ts = (START_DATE + timedelta(days=1)).replace(
    hour=12, minute=30, second=0
)

for i in range(35):
    user = random.choice(STUDENTS)
    profile = student_profiles[user]
    device = random.choice(profile["devices"])
    rows.append({
        "Timestamp":        overload_ts.strftime("%Y-%m-%d %H:%M:%S"),
        "Username":         user,
        "MAC_Address":      device["mac"],
        "IP_Address":       device["ip"],
        "Device_Name":      device["device_name"],
        "Device_Type":      device["device_type"],
        "SSID":             "VIIT-Student",
        "Access_Point":     "AP-CAFE-01",
        "Website":          "youtube.com",
        "Website_Category": "Streaming",
        "Upload_MB":        round(random.uniform(1, 50), 2),
        "Download_MB":      round(random.uniform(50, 500), 2),
        "Status":           "Allowed",
    })

# =============================================================
# Sort by Timestamp and Write CSV
# =============================================================

rows.sort(key=lambda r: r["Timestamp"])

FIELDNAMES = [
    "Timestamp", "Username", "MAC_Address", "IP_Address",
    "Device_Name", "Device_Type", "SSID", "Access_Point",
    "Website", "Website_Category", "Upload_MB", "Download_MB", "Status"
]

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

print(f"Dataset generated successfully!")
print(f"File   : {OUTPUT_FILE}")
print(f"Rows   : {len(rows)}")
print(f"Columns: {len(FIELDNAMES)}")
print()
print("Anomalies embedded:")
high_upload_users = [u for u, p in student_profiles.items() if p["anomaly"] == "high_upload"]
blocked_users     = [u for u, p in student_profiles.items() if p["anomaly"] == "blocked_repeater"]
multi_dev_users   = [u for u, p in student_profiles.items() if len(p["devices"]) >= 3]
print(f"  High upload users      : {len(high_upload_users)} → {high_upload_users}")
print(f"  Blocked site repeaters : {len(blocked_users)} → {blocked_users}")
print(f"  Multi-device users (3+): {len(multi_dev_users)} → {multi_dev_users}")
print(f"  Overloaded AP scenario : AP-CAFE-01 at 2024-11-05 12:30:00 (35 users)")
