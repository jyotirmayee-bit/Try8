"""
Home.py
-------
The ENTIRE dashboard lives in this one file -- Cluster Dashboard AND every
Unit Dashboard. Use the dropdown in the sidebar to switch views.
No pages/ folder needed any more.

Run with:  streamlit run Home.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_loader import load_master_data
from utils import (
    add_status_column, department_summary, compute_conversion_metrics,
    build_kpi_trend, build_department_trend, THEME, TREEMAP_SEQUENCE,
)
from config import DEPARTMENTS
from logo_data import LOGO_BASE64

st.set_page_config(
    page_title="Srikara Hospitals | Dashboard",
    page_icon="🏥",
    layout="wide",
)

st.markdown("""
<style>
    /* ---------- Overall app background ---------- */
    .stApp {
        background-color: #f4f9f9;
    }

    /* ---------- Logo / hospital banner ---------- */
    .srikara-banner {
        display: flex;
        align-items: center;
        gap: 18px;
        background: linear-gradient(135deg, #0b5f6b 0%, #0e7c86 100%);
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(11, 95, 107, 0.25);
    }
    .srikara-banner .logo-badge {
        width: 64px;
        height: 64px;
        min-width: 64px;
        border-radius: 50%;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        padding: 6px;
    }
    .srikara-banner .logo-badge img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    .srikara-banner .banner-text h1 {
        color: #ffffff !important;
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0;
        line-height: 1.15;
        text-shadow: 0 1px 3px rgba(0,0,0,0.25);
    }
    .srikara-banner .banner-text p {
        color: #eaf7f5 !important;
        font-size: 1rem;
        margin: 4px 0 0 0;
        font-weight: 500;
    }

    /* ---------- KPI metric cards ---------- */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d8e8e6;
        border-left: 5px solid #0b5f6b;
        border-radius: 12px;
        padding: 16px 18px 12px 18px;
        box-shadow: 0 2px 6px rgba(11, 95, 107, 0.07);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        color: #0b5f6b !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #355359 !important;
    }

    /* ---------- Headings ---------- */
    h1 { color: #0b5f6b; font-weight: 800; }
    h2, h3 { color: #0b5f6b; font-weight: 700; }
    .stApp p, .stApp label, .stApp span { color: #2b3a3d; }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background-color: #eef6f5;
        border-right: 1px solid #d8e8e6;
    }
    section[data-testid="stSidebar"] h3 {
        color: #0b5f6b;
        font-weight: 800;
    }

    /* ---------- Section radio buttons (look like professional tabs) ---------- */
    div[role="radiogroup"] label {
        background: #ffffff;
        border: 1px solid #d8e8e6;
        border-radius: 8px;
        padding: 6px 14px;
        margin-right: 6px;
        font-weight: 600;
        color: #0b5f6b;
    }

    /* ---------- Department cards ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border: 1px solid #d8e8e6 !important;
        background: #ffffff !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] h3 {
        font-size: 1.15rem !important;
        color: #0b5f6b !important;
    }

    /* ---------- Dataframes ---------- */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #d8e8e6;
    }
</style>
""", unsafe_allow_html=True)


def render_logo_banner(subtitle: str):
    """Professional hospital-style banner with the real Srikara logo, shown at the top of every view."""
    st.markdown(f"""
    <div class="srikara-banner">
        <div class="logo-badge">
            <img src="data:image/png;base64,{LOGO_BASE64}" alt="Srikara Hospitals logo" />
        </div>
        <div class="banner-text">
            <h1>SRIKARA HOSPITALS</h1>
            <p>{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Load data ONCE, shared by every view
# ---------------------------------------------------------------------
raw_df = load_master_data()
df = add_status_column(raw_df)
summary_df = department_summary(df)

# ---------------------------------------------------------------------
# Sidebar: pick which view to show
# ---------------------------------------------------------------------
VIEW_OPTIONS = ["🏠 Cluster Dashboard"] + [f"{d['icon']} {d['name']}" for d in DEPARTMENTS]


def go_to_department(dept_name: str, dept_icon: str):
    """Helper so buttons on the Cluster Dashboard can jump straight to a unit view."""
    st.session_state["_pending_view"] = f"{dept_icon} {dept_name}"
    st.rerun()


def go_to_cluster_dashboard():
    """Helper so the 'Back to Cluster Dashboard' button can jump back."""
    st.session_state["_pending_view"] = "🏠 Cluster Dashboard"
    st.rerun()


# Apply any pending navigation request BEFORE the radio widget below is
# instantiated -- this is the only point in the run where it's legal to
# set a widget's own session-state key, and it's what makes the selection
# actually stick (not just for the next single rerun, but for good).
if "_pending_view" in st.session_state:
    st.session_state["sidebar_view_selector"] = st.session_state.pop("_pending_view")

with st.sidebar:
    st.markdown("### 🏥 Srikara Hospitals")
    selected_view = st.radio("Choose a dashboard", VIEW_OPTIONS, index=0, key="sidebar_view_selector")
    st.divider()
    st.caption("Data refreshes every 5 minutes.")


# =======================================================================
# VIEW: CLUSTER DASHBOARD
# =======================================================================
def render_cluster_dashboard():
    render_logo_banner("Cluster Dashboard &nbsp;•&nbsp; Executive overview across all departments")

    f1, f2, f3 = st.columns([2, 1.2, 2])
    with f1:
        dept_filter = st.multiselect(
            "Filter by department",
            options=[d["name"] for d in DEPARTMENTS],
            default=[],
            placeholder="All departments",
        )
    with f2:
        status_filter = st.multiselect(
            "Filter by status",
            options=["On Track", "Off Track", "No Data", "Not Measurable"],
            default=[],
            placeholder="All statuses",
        )
    with f3:
        search_text = st.text_input("Search KPI name", placeholder="e.g. bed occupancy, mortality...")

    filtered_df = df.copy()
    if dept_filter:
        filtered_df = filtered_df[filtered_df["Department"].isin(dept_filter)]
    if status_filter:
        filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]
    if search_text:
        filtered_df = filtered_df[filtered_df["Particulars"].str.contains(search_text, case=False, na=False)]

    filtered_summary = department_summary(filtered_df) if len(filtered_df) else summary_df.iloc[0:0]

    st.divider()

    section = st.radio(
        "Section",
        ["📊 Overview", "📈 Trends & Conversion", "🔍 Department Deep-Dive", "📋 Raw Data"],
        horizontal=True,
        label_visibility="collapsed",
        key="cluster_section_selector",
    )

    # --- SECTION: OVERVIEW ---
    if section == "📊 Overview":
        total_kpis = len(filtered_df)
        on_track = int((filtered_df["Status"] == "On Track").sum())
        off_track = int((filtered_df["Status"] == "Off Track").sum())
        no_data = int((filtered_df["Status"] == "No Data").sum())
        measurable = on_track + off_track
        overall_health = round((on_track / measurable) * 100, 1) if measurable else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total KPIs Tracked", total_kpis)
        c2.metric("🟢 On Track", on_track)
        c3.metric("🔴 Off Track", off_track)
        c4.metric("⚪ Awaiting Data", no_data)
        c5.metric("Overall Health Score", f"{overall_health}%")

        st.divider()

        left, mid, right = st.columns([1.3, 1.7, 1.3])
        with left:
            st.subheader("Overall Health Gauge")
            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=overall_health,
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": THEME["primary"]},
                    "steps": [
                        {"range": [0, 50], "color": "#fee2e2"},
                        {"range": [50, 80], "color": "#fef3c7"},
                        {"range": [80, 100], "color": "#dcfce7"},
                    ],
                    "threshold": {"line": {"color": "red", "width": 3}, "value": 80},
                },
            ))
            gauge.update_layout(margin=dict(t=30, b=10, l=20, r=20), height=280)
            st.plotly_chart(gauge, use_container_width=True, key="cluster_gauge")

        with mid:
            st.subheader("Department-wise KPI Status")
            if len(filtered_summary):
                chart_df = filtered_summary.melt(
                    id_vars="Department",
                    value_vars=["On Track", "Off Track", "No Data", "Not Measurable"],
                    var_name="Status", value_name="Count",
                )
                fig = px.bar(chart_df, x="Department", y="Count", color="Status",
                             color_discrete_map=THEME, barmode="stack")
                fig.update_layout(xaxis_tickangle=-30, legend_title_text="", margin=dict(t=10), height=280)
                st.plotly_chart(fig, use_container_width=True, key="cluster_status_bar")
            else:
                st.info("No data matches the current filters.")

        with right:
            st.subheader("Overall Health")
            if len(filtered_df):
                donut_df = filtered_df["Status"].value_counts().reset_index()
                donut_df.columns = ["Status", "Count"]
                fig2 = px.pie(donut_df, names="Status", values="Count", hole=0.55,
                              color="Status", color_discrete_map=THEME)
                fig2.update_layout(showlegend=True, margin=dict(t=10), height=280)
                st.plotly_chart(fig2, use_container_width=True, key="cluster_donut")
            else:
                st.info("No data to show.")

        st.divider()
        st.subheader("KPI Distribution (Treemap)")
        st.caption("Box size = number of KPIs, color = status.")
        if len(filtered_df):
            treemap_df = filtered_df.groupby(["Department", "Status"]).size().reset_index(name="Count")
            fig_tree = px.treemap(treemap_df, path=["Department", "Status"], values="Count",
                                   color="Status", color_discrete_map=THEME,
                                   color_discrete_sequence=TREEMAP_SEQUENCE)
            fig_tree.update_traces(
                textfont=dict(color="#22333a", size=14, family="Arial Black"),
                marker=dict(line=dict(color="#ffffff", width=2)),
            )
            fig_tree.update_layout(margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_tree, use_container_width=True, key="cluster_treemap")
        else:
            st.info("No data matches the current filters.")

        st.divider()
        st.subheader("Department Health Score Ranking")
        if len(filtered_summary):
            ranked = filtered_summary.sort_values("Health Score", ascending=True)
            fig3 = px.bar(ranked, x="Health Score", y="Department", orientation="h",
                          color="Health Score", color_continuous_scale=["#f08a8a", "#e0b45c", "#6fbf9b"],
                          range_color=[0, 100], text="Health Score")
            fig3.update_traces(texttemplate="%{text}%", textposition="outside")
            fig3.update_layout(coloraxis_showscale=False, margin=dict(t=10), xaxis_range=[0, 110])
            st.plotly_chart(fig3, use_container_width=True, key="cluster_health_ranking")
        else:
            st.info("No data matches the current filters.")

        st.divider()
        st.subheader("⚠️ Departments Needing Attention")
        if len(filtered_summary):
            attention = filtered_summary[filtered_summary["Off Track"] > 0].sort_values("Off Track", ascending=False)
            if len(attention):
                st.dataframe(attention[["Department", "Off Track", "On Track", "Total KPIs", "Health Score"]],
                             use_container_width=True, hide_index=True)
            else:
                st.success("No departments have off-track KPIs right now. 🎉")

        st.divider()
        st.subheader("Open a Unit Dashboard")
        cols = st.columns(3)
        for i, dept in enumerate(DEPARTMENTS):
            dept_rows = summary_df[summary_df["Department"] == dept["name"]]
            total = int(dept_rows["Total KPIs"].iloc[0]) if not dept_rows.empty else 0
            off = int(dept_rows["Off Track"].iloc[0]) if not dept_rows.empty else 0
            health = float(dept_rows["Health Score"].iloc[0]) if not dept_rows.empty else 0

            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"### {dept['icon']} {dept['name']}")
                    st.caption(f"{total} KPIs • {off} off track • {health}% healthy")
                    if st.button("Open Unit Dashboard →", key=f"jump_{dept['name']}", use_container_width=True):
                        go_to_department(dept["name"], dept["icon"])

    # --- SECTION: TRENDS & CONVERSION ---
    elif section == "📈 Trends & Conversion":
        st.subheader("Cluster-wide Trend: Last Month → MTD → Today")
        st.caption("Total of every numeric KPI in the sheet, added up across all departments, at each snapshot.")

        trend_rows = []
        for period in ["Last Month", "MTD", "Today"]:
            numeric = pd.to_numeric(filtered_df[period], errors="coerce").dropna()
            if len(numeric):
                trend_rows.append({"Period": period, "Total": numeric.sum()})
        trend_df = pd.DataFrame(trend_rows)

        if len(trend_df) >= 2:
            trend_df["Period"] = pd.Categorical(trend_df["Period"], ["Last Month", "MTD", "Today"], ordered=True)
            trend_df = trend_df.sort_values("Period")
            fig4 = px.area(trend_df, x="Period", y="Total", markers=True)
            fig4.update_traces(line_color=THEME["primary"], fillcolor="rgba(15,76,129,0.15)",
                               line_width=3, marker_size=10)
            fig4.update_layout(margin=dict(t=10))
            st.plotly_chart(fig4, use_container_width=True, key="cluster_trend_area")
        else:
            st.info("Not enough numeric data across Last Month / MTD / Today yet to plot a trend.")

        st.divider()
        st.subheader("🔄 Conversion Metrics")
        st.caption("Automatically detected funnel rates, e.g. how many OPD visitors convert to admissions.")
        conversions = compute_conversion_metrics(df)
        if conversions:
            cols = st.columns(len(conversions))
            for col, conv in zip(cols, conversions):
                with col:
                    st.metric(conv["label"], f"{conv['rate']}%", help=conv["help"])
                    st.caption(f"{conv['numerator_label']} ÷ {conv['denominator_label']}")

            st.markdown("#### Funnel View")
            for conv in conversions:
                fig_funnel = go.Figure(go.Funnel(
                    y=[conv["denominator_label"], conv["numerator_label"]],
                    x=[100, conv["rate"]],
                    textinfo="value+percent initial",
                    marker={"color": [THEME["primary"], THEME["accent"]]},
                ))
                fig_funnel.update_layout(title=conv["label"], margin=dict(t=40, b=10), height=260)
                st.plotly_chart(fig_funnel, use_container_width=True, key=f"funnel_{conv['label']}")
        else:
            st.info(
                "No matching KPI pairs found yet to calculate a conversion rate. "
                "Once the sheet has clearly labeled footfall/admission-type rows with 'Today' values filled in, "
                "conversion rates will appear here automatically."
            )

    # --- SECTION: DEEP DIVE ---
    elif section == "🔍 Department Deep-Dive":
        st.subheader("Compare Departments Side-by-Side")
        compare_depts = st.multiselect(
            "Choose departments to compare",
            options=[d["name"] for d in DEPARTMENTS],
            default=[d["name"] for d in DEPARTMENTS[:3]],
        )
        if compare_depts:
            compare_df = filtered_summary[filtered_summary["Department"].isin(compare_depts)]
            if len(compare_df):
                fig5 = px.bar(compare_df, x="Department", y="Health Score", color="Department", text="Health Score")
                fig5.update_traces(texttemplate="%{text}%", textposition="outside")
                fig5.update_layout(showlegend=False, margin=dict(t=10), yaxis_range=[0, 110])
                st.plotly_chart(fig5, use_container_width=True, key="deepdive_bar")

                st.dataframe(
                    compare_df[["Department", "On Track", "Off Track", "No Data", "Total KPIs", "Health Score"]],
                    use_container_width=True, hide_index=True,
                )

                st.divider()
                radar_col, bubble_col = st.columns(2)
                with radar_col:
                    st.markdown("#### Radar Comparison")
                    radar_fig = go.Figure()
                    categories = ["On Track", "Off Track", "Health Score"]
                    for _, row in compare_df.iterrows():
                        values = [row["On Track"], row["Off Track"], row["Health Score"] / 10]
                        radar_fig.add_trace(go.Scatterpolar(
                            r=values + values[:1], theta=categories + categories[:1],
                            fill="toself", name=row["Department"],
                        ))
                    radar_fig.update_layout(margin=dict(t=10), height=380)
                    st.plotly_chart(radar_fig, use_container_width=True, key="deepdive_radar")

                with bubble_col:
                    st.markdown("#### Size vs Health Bubble Chart")
                    bubble_fig = px.scatter(compare_df, x="Total KPIs", y="Health Score", size="Off Track",
                                            color="Department", size_max=45, text="Department")
                    bubble_fig.update_traces(textposition="top center")
                    bubble_fig.update_layout(margin=dict(t=10), height=380, yaxis_range=[-5, 110], showlegend=False)
                    st.plotly_chart(bubble_fig, use_container_width=True, key="deepdive_bubble")
            else:
                st.info("No data for the selected departments under the current filters.")
        else:
            st.info("Pick at least one department above to compare.")

    # --- SECTION: RAW DATA ---
    elif section == "📋 Raw Data":
        st.subheader("Hierarchical View (Sunburst)")
        if len(filtered_df):
            sunburst_df = filtered_df.groupby(["Department", "Status"]).size().reset_index(name="Count")
            fig_sun = px.sunburst(sunburst_df, path=["Department", "Status"], values="Count",
                                  color="Status", color_discrete_map=THEME,
                                  color_discrete_sequence=TREEMAP_SEQUENCE)
            fig_sun.update_traces(
                textfont=dict(color="#22333a", size=13, family="Arial Black"),
                marker=dict(line=dict(color="#ffffff", width=2)),
            )
            fig_sun.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=500)
            st.plotly_chart(fig_sun, use_container_width=True, key="cluster_sunburst")

        st.divider()
        st.subheader("Full KPI Table")
        display_cols = ["Department", "Particulars", "Today", "MTD", "Target", "Last Month",
                        "Achievement %", "Status Icon", "Status"]
        display_cols = [c for c in display_cols if c in filtered_df.columns]
        st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

        csv_bytes = filtered_df[display_cols].to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download this view as CSV", data=csv_bytes,
                           file_name="srikara_cluster_dashboard.csv", mime="text/csv")

    st.divider()
    st.caption("Data source: Srikara Hospitals Unit Tracker (Google Sheet) • Auto-refreshes every 5 minutes")


# =======================================================================
# VIEW: UNIT DASHBOARD (one department)
# =======================================================================
def render_unit_dashboard(dept_name: str, dept_icon: str, dept_owner: str):
    if st.button("← Back to Cluster Dashboard"):
        go_to_cluster_dashboard()

    render_logo_banner(f"{dept_icon} {dept_name} Unit Dashboard &nbsp;•&nbsp; Owner: {dept_owner}")

    dept_df = df[df["Department"] == dept_name].reset_index(drop=True)
    if dept_df.empty:
        st.warning("No KPI rows found for this department in the sheet yet.")
        return

    on_track = int((dept_df["Status"] == "On Track").sum())
    off_track = int((dept_df["Status"] == "Off Track").sum())
    no_data = int((dept_df["Status"] == "No Data").sum())
    measurable = on_track + off_track
    health_score = round((on_track / measurable) * 100, 1) if measurable else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total KPIs", len(dept_df))
    c2.metric("🟢 On Track", on_track)
    c3.metric("🔴 Off Track", off_track)
    c4.metric("⚪ Awaiting Data", no_data)
    c5.metric("Health Score", f"{health_score}%")

    st.divider()

    unit_section = st.radio(
        "Unit section",
        ["🎯 KPI Detail", "📈 Trend", "📋 Full Data"],
        horizontal=True,
        label_visibility="collapsed",
        key="unit_section_selector",
    )

    # --- KPI DETAIL ---
    if unit_section == "🎯 KPI Detail":
        gauge_col, donut_col = st.columns(2)
        with gauge_col:
            st.markdown("#### Health Gauge")
            gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=health_score, number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]}, "bar": {"color": THEME["primary"]},
                    "steps": [
                        {"range": [0, 50], "color": "#fee2e2"},
                        {"range": [50, 80], "color": "#fef3c7"},
                        {"range": [80, 100], "color": "#dcfce7"},
                    ],
                },
            ))
            gauge.update_layout(margin=dict(t=20, b=10, l=20, r=20), height=250)
            st.plotly_chart(gauge, use_container_width=True, key="unit_gauge")

        with donut_col:
            st.markdown("#### Status Breakdown")
            status_counts = dept_df["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            donut = px.pie(status_counts, names="Status", values="Count", hole=0.55,
                           color="Status", color_discrete_map=THEME)
            donut.update_layout(margin=dict(t=20, b=10), height=250)
            st.plotly_chart(donut, use_container_width=True, key="unit_donut")

        st.divider()
        st.markdown("#### Achievement % by KPI (ranked)")
        ranked_df = dept_df.dropna(subset=["Achievement %"]).sort_values("Achievement %")
        if len(ranked_df):
            fig_rank = px.bar(ranked_df, x="Achievement %", y="Particulars", orientation="h",
                              color="Status", color_discrete_map=THEME, text="Achievement %")
            fig_rank.update_traces(texttemplate="%{text}%", textposition="outside")
            fig_rank.update_layout(margin=dict(t=10), height=max(250, 40 * len(ranked_df)))
            st.plotly_chart(fig_rank, use_container_width=True, key="unit_achievement_rank")
        else:
            st.info("No KPIs with a numeric target/achievement value yet.")

        st.divider()
        search = st.text_input(f"Search KPIs in {dept_name}", placeholder="e.g. mortality, occupancy...")
        view_df = dept_df.copy()
        if search:
            view_df = view_df[view_df["Particulars"].str.contains(search, case=False, na=False)]

        if view_df.empty:
            st.info("No KPIs match your search.")
        else:
            for _, row in view_df.iterrows():
                with st.container(border=True):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(
                            f"<span style='font-size:1.15rem; font-weight:700; color:#0b5f6b;'>{row['Particulars']}</span>",
                            unsafe_allow_html=True,
                        )
                        st.caption(
                            f"Today: {row.get('Today', 'N/A')} • MTD: {row.get('MTD', 'N/A')} • "
                            f"Target: {row.get('Target', 'N/A')} • Last Month: {row.get('Last Month', 'N/A')}"
                        )
                        achievement = row.get("Achievement %")
                        if achievement is not None and pd.notna(achievement):
                            bar_value = max(0, min(int(achievement), 100))
                            st.progress(bar_value, text=f"{achievement}% of target")
                    with col_b:
                        st.markdown(
                            f"<div style='text-align:center; font-size:1.8rem;'>{row['Status Icon']}</div>"
                            f"<div style='text-align:center; font-size:0.85rem; color:gray;'>{row['Status']}</div>",
                            unsafe_allow_html=True,
                        )

    # --- TREND ---
    elif unit_section == "📈 Trend":
        st.subheader("Department Trend: Last Month → MTD → Today")
        dept_trend = build_department_trend(dept_df)
        if len(dept_trend) >= 2:
            dept_trend["Period"] = pd.Categorical(dept_trend["Period"], ["Last Month", "MTD", "Today"], ordered=True)
            dept_trend = dept_trend.sort_values("Period")
            fig = px.area(dept_trend, x="Period", y="Total", markers=True)
            fig.update_traces(line_color=THEME["primary"], fillcolor="rgba(15,76,129,0.15)",
                              line_width=3, marker_size=10)
            fig.update_layout(margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True, key="unit_trend_area")
        else:
            st.info("Not enough numeric data yet across Last Month / MTD / Today to plot a trend.")

        st.divider()
        st.subheader("Individual KPI Trends")
        for idx, row in dept_df.iterrows():
            kpi_trend = build_kpi_trend(row)
            if len(kpi_trend) >= 2:
                with st.expander(row["Particulars"]):
                    fig2 = px.bar(kpi_trend, x="Period", y="Value", text="Value")
                    fig2.update_traces(marker_color=THEME["accent"])
                    fig2.update_layout(margin=dict(t=10), height=280)
                    st.plotly_chart(fig2, use_container_width=True, key=f"kpi_trend_{dept_name}_{idx}")

    # --- FULL DATA ---
    elif unit_section == "📋 Full Data":
        display_cols = ["Particulars", "Today", "MTD", "Target", "Last Month",
                        "Achievement %", "Status Icon", "Status"]
        display_cols = [c for c in display_cols if c in dept_df.columns]
        st.dataframe(dept_df[display_cols], use_container_width=True, hide_index=True)

        slug = dept_name.lower().replace(" ", "_").replace("&", "and")
        csv_bytes = dept_df[display_cols].to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download this department's data as CSV", data=csv_bytes,
                           file_name=f"{slug}.csv", mime="text/csv")


# =======================================================================
# ROUTER: decide which view to render based on the sidebar selection
# =======================================================================
if selected_view == "🏠 Cluster Dashboard":
    render_cluster_dashboard()
else:
    matched = next((d for d in DEPARTMENTS if f"{d['icon']} {d['name']}" == selected_view), None)
    if matched:
        render_unit_dashboard(matched["name"], matched["icon"], matched["owner"])
    else:
        st.error("Unknown view selected. Please choose again from the sidebar.")
