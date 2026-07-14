"""
utils.py
--------
Shared helper functions for the whole dashboard:
- parsing targets & computing On Track / Off Track status
- achievement % (how close a KPI is to its target)
- building 3-point trend data (Last Month -> MTD -> Today)
- conversion-rate metrics (e.g. OPD footfall -> IP admission)
- shared color theme
"""

import re
import pandas as pd

# ---------------------------------------------------------------------------
# COLOR THEME  (used everywhere so every chart/page looks consistent)
# A fresh, light "hospital" palette -- deep teal as the anchor color for
# headings/branding, softer pastel tones for chart status colors so the
# dashboard reads as calm and clinical rather than alarm-heavy.
# ---------------------------------------------------------------------------
THEME = {
    "On Track": "#9bd4b8",       # light pastel mint-green
    "Off Track": "#f2a8a8",      # light pastel coral-red
    "No Data": "#d5dae0",        # very light pastel gray
    "Not Measurable": "#aecbe8", # light pastel sky blue
    "primary": "#0b5f6b",        # deep teal -- the hospital's anchor color (kept for headings/branding)
    "secondary": "#0e7c86",      # lighter teal for gradients/accents
    "accent": "#e8c581",         # light pastel gold accent (used sparingly)
    "background": "#f4f9f9",     # very light teal-tinted background
}

# Soft pastel palette used for treemap/sunburst PARENT-level boxes (e.g. each
# Department), so those boxes read as fresh and light rather than the bold
# default plotly qualitative colors.
TREEMAP_SEQUENCE = [
    "#dcebe8", "#e5e0f0", "#faeae3", "#e3f0de", "#faf0d2",
    "#e0edf6", "#f5e5ee", "#e6f2f2", "#f0e9dd", "#e5eaf5",
]

STATUS_COLORS = {
    "On Track": "🟢",
    "Off Track": "🔴",
    "No Data": "⚪",
    "Not Measurable": "🔵",
}


# ---------------------------------------------------------------------------
# TARGET PARSING
# ---------------------------------------------------------------------------
def _to_number(text):
    """Pulls the first number out of a string like '>=150/day' -> 150.0"""
    if text is None:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", str(text).replace(",", ""))
    return float(match.group()) if match else None


def parse_target(target_text):
    """
    Splits a target string into (operator, number).
    Examples:
        '>=150/day'  -> ('>=', 150.0)
        '<=3.5 days' -> ('<=', 3.5)
        '<5%'        -> ('<', 5.0)
        '100%'       -> ('=', 100.0)
        'Monitor'    -> (None, None)   # not a numeric target
    """
    if target_text is None or str(target_text).strip().lower() in ("nan", "monitor", "track only", ""):
        return None, None

    text = str(target_text).strip()
    if text.startswith(">="):
        return ">=", _to_number(text)
    if text.startswith("<="):
        return "<=", _to_number(text)
    if text.startswith(">"):
        return ">", _to_number(text)
    if text.startswith("<"):
        return "<", _to_number(text)
    number = _to_number(text)
    return ("=", number) if number is not None else (None, None)


def compute_status(today_value, target_text):
    """
    Compares today's value against the target and returns one of:
    'On Track', 'Off Track', 'No Data', 'Not Measurable'
    """
    today_number = _to_number(today_value)
    operator, target_number = parse_target(target_text)

    if today_number is None:
        return "No Data"
    if operator is None or target_number is None:
        return "Not Measurable"

    checks = {
        ">=": today_number >= target_number,
        "<=": today_number <= target_number,
        ">": today_number > target_number,
        "<": today_number < target_number,
        "=": today_number == target_number,
    }
    return "On Track" if checks.get(operator, False) else "Off Track"


def achievement_percentage(today_value, target_text):
    """
    Returns how close 'today' is to the target, as a percentage.
    - For >=/>/'=' targets: 100% means target met exactly, over 100% means exceeded.
    - For <=/< targets (lower is better, e.g. mortality rate, LAMA %):
      100% means target met exactly; the calc is inverted so a SMALLER
      actual value still shows as a HIGH (good) percentage.
    Returns None when it can't be computed (missing data or non-numeric target).
    """
    today_number = _to_number(today_value)
    operator, target_number = parse_target(target_text)

    if today_number is None or target_number in (None, 0):
        return None

    if operator in (">=", ">", "="):
        pct = (today_number / target_number) * 100
    elif operator in ("<=", "<"):
        pct = (target_number / today_number) * 100 if today_number != 0 else None
    else:
        return None

    return round(pct, 1) if pct is not None else None


def add_status_column(df: pd.DataFrame) -> pd.DataFrame:
    """Adds 'Status', 'Status Icon' and 'Achievement %' columns to a KPI dataframe."""
    df = df.copy()
    df["Status"] = df.apply(lambda row: compute_status(row.get("Today"), row.get("Target")), axis=1)
    df["Status Icon"] = df["Status"].map(STATUS_COLORS)
    df["Achievement %"] = df.apply(lambda row: achievement_percentage(row.get("Today"), row.get("Target")), axis=1)
    return df


def department_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given the full master dataframe (already has a Status column),
    returns one row per department with counts of On Track / Off Track / No Data,
    plus an overall Health Score (% of measurable KPIs that are On Track).
    """
    summary = (
        df.groupby("Department")["Status"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["On Track", "Off Track", "No Data", "Not Measurable"]:
        if col not in summary.columns:
            summary[col] = 0
    summary["Total KPIs"] = summary[["On Track", "Off Track", "No Data", "Not Measurable"]].sum(axis=1)
    measurable = summary["On Track"] + summary["Off Track"]
    safe_denominator = measurable.replace(0, float("nan"))
    health = (summary["On Track"] / safe_denominator) * 100
    summary["Health Score"] = health.fillna(0).round(1)
    return summary


# ---------------------------------------------------------------------------
# TREND DATA (Last Month -> MTD -> Today)
# The sheet only gives us 3 time snapshots per KPI, but that's enough for a
# simple, honest trend line rather than a single flat number.
# ---------------------------------------------------------------------------
def build_kpi_trend(row: pd.Series) -> pd.DataFrame:
    """Builds a tidy 3-point trend dataframe for a single KPI row."""
    periods = ["Last Month", "MTD", "Today"]
    values = [_to_number(row.get(p)) for p in periods]
    return pd.DataFrame({"Period": periods, "Value": values}).dropna(subset=["Value"])


def build_department_trend(dept_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates numeric KPI values across a department for each of the 3
    periods, so the Unit dashboard can show one overall trend line.
    """
    rows = []
    for period in ["Last Month", "MTD", "Today"]:
        numeric = dept_df[period].apply(_to_number) if period in dept_df.columns else pd.Series(dtype=float)
        numeric = numeric.dropna()
        if len(numeric):
            rows.append({"Period": period, "Total": numeric.sum(), "KPI Count": len(numeric)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# CONVERSION METRICS
# Looks for common hospital funnel pairs (e.g. OPD footfall -> IP admission)
# by keyword-matching the 'Particulars' column. Silently returns nothing if
# a sheet doesn't have matching rows -- never crashes the app.
# ---------------------------------------------------------------------------
CONVERSION_RULES = [
    {
        "label": "OPD -> IP Conversion",
        "numerator_keywords": ["admission", "admit"],
        "numerator_department": "IP Operations",
        "denominator_keywords": ["opd footfall", "opd visit", "out patient", "footfall"],
        "denominator_department": "OPD Operations",
        "help": "% of OPD visitors who were admitted as inpatients",
    },
    {
        "label": "ER -> Admission Rate",
        "numerator_keywords": ["admission", "admit"],
        "numerator_department": "Emergency",
        "denominator_keywords": ["er footfall", "emergency visit", "casualty", "footfall"],
        "denominator_department": "Emergency",
        "help": "% of Emergency visits that resulted in an admission",
    },
    {
        "label": "OT Utilization",
        "numerator_keywords": ["surgeries performed", "surgery", "ot cases"],
        "numerator_department": "OT Operations",
        "denominator_keywords": ["ot slots", "scheduled", "ot capacity"],
        "denominator_department": "OT Operations",
        "help": "% of scheduled OT slots actually utilized",
    },
]


def _find_value(df: pd.DataFrame, keywords, department=None):
    """
    Finds the first 'Today' numeric value whose Particulars text matches any keyword.
    If 'department' is given, only looks within that department's rows first,
    which avoids accidentally matching a similarly-worded KPI from another unit.
    """
    if "Particulars" not in df.columns:
        return None, None

    search_df = df
    if department is not None and "Department" in df.columns:
        scoped = df[df["Department"] == department]
        if not scoped.empty:
            search_df = scoped

    mask = search_df["Particulars"].str.lower().apply(
        lambda text: any(k in text for k in keywords) if isinstance(text, str) else False
    )
    matches = search_df[mask]
    if matches.empty:
        return None, None
    value = _to_number(matches.iloc[0].get("Today"))
    label = matches.iloc[0].get("Particulars")
    return value, label


def compute_conversion_metrics(df: pd.DataFrame):
    """
    Scans the master dataframe for conversion-rate opportunities, scoped to the
    relevant department for each rule so KPIs from different units don't get
    mixed up. Returns a list of dicts:
    {label, help, rate, numerator_label, denominator_label}
    Only includes rules where BOTH sides of the ratio were found in the sheet.
    """
    results = []
    for rule in CONVERSION_RULES:
        num_value, num_label = _find_value(df, rule["numerator_keywords"], rule.get("numerator_department"))
        den_value, den_label = _find_value(df, rule["denominator_keywords"], rule.get("denominator_department"))
        if num_value is not None and den_value not in (None, 0):
            rate = round((num_value / den_value) * 100, 1)
            results.append({
                "label": rule["label"],
                "help": rule["help"],
                "rate": rate,
                "numerator_label": num_label,
                "denominator_label": den_label,
            })
    return results
