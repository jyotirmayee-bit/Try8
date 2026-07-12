"""
config.py
---------
All the settings for the dashboard live here.
If the Google Sheet ever changes, this is the ONLY file you should need to edit.
"""

# The long ID in your Google Sheet URL (the part between /d/ and /edit)
SHEET_ID = "1PCEbzi2RLDSV--bbDwaRMob2nU33PULlyjJp9Xwwv9M"

# The GID of the master "Unit Tracker" tab (the one with every department listed).
# You can see this number in the URL after gid= when that tab is open.
MASTER_GID = "143552182"

SHEET_GIDS = {
    # "OP Incharge": "PASTE_GID_HERE",
    # "IP Incharge": "PASTE_GID_HERE",
    # "ICU Incharge": "PASTE_GID_HERE",
    # "ER": "PASTE_GID_HERE",
    # "OT Incharge": "PASTE_GID_HERE",
    # "Billing": "PASTE_GID_HERE",
    # "Pharmacy": "PASTE_GID_HERE",
    # "Lab": "PASTE_GID_HERE",
    # "Radiology": "PASTE_GID_HERE",
    # "Quality Head": "PASTE_GID_HERE",
    # "MS": "PASTE_GID_HERE",
    # "Medical Admin": "PASTE_GID_HERE",
    # "Unit Head": "PASTE_GID_HERE",
    # "IT": "PASTE_GID_HERE",
}

# Every department found in the master tab, and its display icon.
# No "page" file path needed any more -- everything lives in one file (Home.py)
# and departments are switched via a sidebar dropdown instead of separate pages.
DEPARTMENTS = [
    {"name": "OPD Operations",     "owner": "OP Incharge",  "icon": "🩺"},
    {"name": "IP Operations",      "owner": "IP Incharge",  "icon": "🛏️"},
    {"name": "ICU Operations",     "owner": "ICU Incharge", "icon": "❤️‍🩹"},
    {"name": "Emergency",          "owner": "ER",           "icon": "🚑"},
    {"name": "OT Operations",      "owner": "OT Incharge",  "icon": "🔪"},
    {"name": "Billing & Revenue",  "owner": "Billing",      "icon": "💵"},
    {"name": "Pharmacy",           "owner": "Pharmacy",     "icon": "💊"},
    {"name": "Laboratory",         "owner": "Lab",          "icon": "🧪"},
    {"name": "Radiology",          "owner": "Radiology",    "icon": "🩻"},
    {"name": "Clinical Quality",   "owner": "Quality Head", "icon": "✅"},
    {"name": "Medical Staff",      "owner": "MS",           "icon": "👩‍⚕️"},
]

CACHE_TTL_SECONDS = 300  # 5 minutes
