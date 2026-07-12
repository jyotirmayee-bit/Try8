"""
data_loader.py
---------------
Everything related to FETCHING data from Google Sheets lives here.
No page needs to know HOW the data is fetched -- it just calls load_master_data().
"""

import pandas as pd
import streamlit as st
from config import SHEET_ID, MASTER_GID, SHEET_GIDS, CACHE_TTL_SECONDS


def _csv_url(gid: str) -> str:
    """Builds the public CSV export URL for a given tab (gid) of the sheet."""
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Fetching latest data from Google Sheets...")
def load_master_data() -> pd.DataFrame:
    """
    Loads the master 'Unit Tracker' tab which lists every KPI for every
    department. This single tab powers both the Cluster dashboard and,
    by filtering, every Unit dashboard.
    """
    url = _csv_url(MASTER_GID)
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(
            "Could not load data from the Google Sheet.\n\n"
            "Please check that:\n"
            "1. The sheet's sharing setting is 'Anyone with the link can view'.\n"
            "2. Your internet connection is working.\n\n"
            f"Technical details: {e}"
        )
        st.stop()

    # --- basic cleanup so the rest of the app can trust the data ---
    df.columns = [str(c).strip() for c in df.columns]

    # Drop fully empty rows (the sheet has many blank trailing rows)
    df = df.dropna(how="all")

    # Make sure the columns we rely on always exist, even if the sheet
    # changes slightly (avoids KeyError crashes).
    expected_cols = ["Sl.No", "Department", "Particulars", "Today", "MTD", "Target", "Last Month", "Ref Sheet"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    # Drop rows where there's no Department AND no Particulars (junk rows)
    df = df.dropna(subset=["Department", "Particulars"], how="all")
    df = df[df["Department"].notna()]

    # Clean whitespace on text columns
    for col in ["Department", "Particulars", "Target", "Ref Sheet"]:
        df[col] = df[col].astype(str).str.strip().replace({"nan": None})

    df = df.reset_index(drop=True)
    return df


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_unit_sheet(gid: str) -> pd.DataFrame:
    """
    Loads a dedicated unit tab (used only once you've filled in SHEET_GIDS
    in config.py). Returns an empty DataFrame if it fails, so a missing GID
    never crashes the app.
    """
    if not gid:
        return pd.DataFrame()
    try:
        return pd.read_csv(_csv_url(gid))
    except Exception:
        return pd.DataFrame()


def filter_by_department(df: pd.DataFrame, department_name: str) -> pd.DataFrame:
    """Returns only the rows belonging to one department."""
    return df[df["Department"] == department_name].reset_index(drop=True)
