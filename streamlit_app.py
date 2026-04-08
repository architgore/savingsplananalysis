import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="AWS Savings Plan Dashboard", layout="wide")

# ----------------------------
# Styling
# ----------------------------
st.markdown(
    """
    <style>
        .main {
            background: #f6f8fc;
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 1600px;
        }
        .hero-card {
            background: linear-gradient(135deg, #0b1f3a 0%, #204e80 55%, #3a6ea5 100%);
            padding: 1.5rem 1.75rem;
            border-radius: 22px;
            color: white;
            box-shadow: 0 12px 30px rgba(11, 31, 58, 0.22);
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
            line-height: 1.1;
        }
        .hero-subtitle {
            font-size: 1rem;
            opacity: 0.95;
            margin-bottom: 0.2rem;
        }
        .hero-note {
            font-size: 0.92rem;
            opacity: 0.82;
            margin-top: 0.4rem;
        }
        .insight-card {
            background: linear-gradient(180deg, #ffffff 0%, #f9fbff 100%);
            border: 1px solid #e8eef7;
            border-radius: 18px;
            padding: 1rem 1rem 0.85rem 1rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
            margin-bottom: 0.8rem;
        }
        .insight-title {
            font-size: 0.82rem;
            font-weight: 700;
            color: #45607d;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }
        .insight-value {
            font-size: 1.45rem;
            font-weight: 800;
            color: #0b1f3a;
            margin-bottom: 0.25rem;
        }
        .insight-text {
            font-size: 0.9rem;
            color: #5d6f85;
            line-height: 1.4;
        }
        .section-card {
            background: #ffffff;
            padding: 1rem 1rem 0.75rem 1rem;
            border-radius: 18px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05);
            border: 1px solid #e9eef6;
            margin-bottom: 1rem;
        }
        .section-label {
            font-size: 0.82rem;
            font-weight: 700;
            color: #597493;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }
        .section-note {
            font-size: 0.90rem;
            color: #5d6f85;
            margin-bottom: 0.75rem;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border-radius: 18px;
            padding: 0.85rem 0.9rem;
            box-shadow: 0 5px 16px rgba(0, 0, 0, 0.05);
            border: 1px solid #e9eef6;
        }
        div[data-testid="stMetricLabel"] {
            color: #5d6f85 !important;
            font-weight: 700 !important;
        }
        div[data-testid="stMetricValue"] {
            color: #0b1f3a !important;
            font-weight: 800 !important;
        }
        h1, h2, h3 {
            color: #0b1f3a;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.55rem 1rem;
            background: #eef3fa;
            border: 1px solid #dde7f4;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background: #0b1f3a !important;
            color: white !important;
            border-color: #0b1f3a !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">AWS Savings Plan Dashboard</div>
        <div class="hero-subtitle">Paramount Savings Plan Analysis</div>
        <div class="hero-note">Executive summary, coverage, uncovered opportunity analysis, inventory, and business group coverage review.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Load data
# ----------------------------
@st.cache_data
def load_data_from_file(file_source):
    df = pd.read_csv(
        file_source,
        low_memory=False,
        usecols=[
            "payer_account_id",
            "business_group",
            "usage_account_id",
            "usage_hour",
            "region",
            "product_name",
            "product_code",
            "instance_type",
            "operatng_system",
            "usage_type",
            "operation",
            "line_item_type",
            "pricing_unit",
            "savings_plan_arn",
            "savings_plan_start_date",
            "savings_plan_end_date",
            "savings_plan_payment_option",
            "savings_plan_purchase_term",
            "usage_amount",
            "ondemand_cost",
            "net_fiscal_cost",
        ],
    )

    df["usage_hour"] = pd.to_datetime(df["usage_hour"], errors="coerce")
    df["savings_plan_start_date"] = pd.to_datetime(
        df["savings_plan_start_date"], errors="coerce", utc=True
    )
    df["savings_plan_end_date"] = pd.to_datetime(
        df["savings_plan_end_date"], errors="coerce", utc=True
    )

    numeric_cols = ["usage_amount", "ondemand_cost", "net_fiscal_cost"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    text_cols = [
        "payer_account_id",
        "business_group",
        "usage_account_id",
        "region",
        "product_name",
        "product_code",
        "instance_type",
        "operatng_system",
        "usage_type",
        "operation",
        "line_item_type",
        "pricing_unit",
        "savings_plan_arn",
        "savings_plan_payment_option",
        "savings_plan_purchase_term",
    ]

    for col in text_cols:
        df[col] = df[col].fillna("Unknown").astype(str)

    df = df.dropna(subset=["usage_hour"])
    df["hour_str"] = df["usage_hour"].dt.strftime("%m/%d/%Y %H:%M")
    df["date"] = df["usage_hour"].dt.date
    df["hour_of_day"] = df["usage_hour"].dt.hour

    df["is_sp_covered"] = (
        df["savings_plan_arn"].str.strip().ne("")
        & df["savings_plan_arn"].ne("Unknown")
    )

    df["covered_cost_proxy"] = np.where(
        df["line_item_type"].eq("SavingsPlanCoveredUsage"),
        df["ondemand_cost"],
        0,
    )
    df["uncovered_cost_proxy"] = np.where(
        df["line_item_type"].eq("Usage"),
        df["ondemand_cost"],
        0,
    )

    return df


# ----------------------------
# Formatting helpers
# ----------------------------
def format_currency(x):
    return f"${round(float(x)):,}"


def format_percent(x):
    return f"{round(float(x))}%"


def format_number(x):
    return f"{round(float(x)):,}"


def format_filtered_date_range(df):
    start_dt = pd.to_datetime(df["usage_hour"].min())
    end_dt = pd.to_datetime(df["usage_hour"].max())

    if pd.isna(start_dt) or pd.isna(end_dt):
        return "N/A"

    if start_dt.date() == end_dt.date():
        return start_dt.strftime("%b %d, %Y")

    if start_dt.year == end_dt.year:
        if start_dt.month == end_dt.month:
            return f"{start_dt.strftime('%b')} {start_dt.day} – {end_dt.day}, {end_dt.year}"
        return f"{start_dt.strftime('%b')} {start_dt.day} – {end_dt.strftime('%b')} {end_dt.day}, {end_dt.year}"

    return f"{start_dt.strftime('%b')} {start_dt.day}, {start_dt.year} – {end_dt.strftime('%b')} {end_dt.day}, {end_dt.year}"


def apply_excel_multiselect_filter(df, column_name, label, sidebar_container):
    options = sorted(df[column_name].dropna().astype(str).unique().tolist())

    if not options:
        return df

    select_all_key = f"{column_name}_select_all"
    selected_key = f"{column_name}_selected"

    select_all = sidebar_container.checkbox(
        f"Select All {label}",
        value=True,
        key=select_all_key,
    )

    default_values = options if select_all else []

    selected = sidebar_container.multiselect(
        label,
        options,
        default=default_values,
        key=selected_key,
    )

    if select_all:
        return df[df[column_name].astype(str).isin(selected)] if selected else df

    return df[df[column_name].astype(str).isin(selected)] if selected else df.iloc[0:0]


recommendation_color_map = {
    "Well covered today": "#2ca02c",
    "Review usage trend": "#f1c40f",
    "Strong candidate for SP review": "#d62728",
    "Monitor for purchase opportunity": "#ff7f0e",
    "Low spend, lower priority": "#7f8c8d",
}


def highlight_row(row):
    color_map_light = {
        "Well covered today": "#e8f5e9",
        "Review usage trend": "#fff9e6",
        "Strong candidate for SP review": "#fdecea",
        "Monitor for purchase opportunity": "#fff3e0",
        "Low spend, lower priority": "#f4f6f7",
    }
    bg_color = color_map_light.get(row["Recommendation"], "#ffffff")
    return [f"background-color: {bg_color}"] * len(row)


# ----------------------------
# Data load
# ----------------------------
st.sidebar.header("Data")
uploaded_file = st.sidebar.file_uploader("Upload Savings Plan CSV", type=["csv"])

if uploaded_file is not None:
    df = load_data_from_file(uploaded_file)
else:
    try:
        df = load_data_from_file("Savings_Plan_Data.csv")
    except FileNotFoundError:
        st.info("Upload a Savings Plan CSV from the sidebar to load the dashboard.")
        st.stop()


# ----------------------------
# Filters
# ----------------------------
st.sidebar.header("Filters")

min_dt = df["usage_hour"].min().date()
max_dt = df["usage_hour"].max().date()
default_start = max(min_dt, max_dt - timedelta(days=30))

selected_dates = st.sidebar.date_input(
    "Usage date range",
    value=(default_start, max_dt),
    min_value=min_dt,
    max_value=max_dt,
)

filtered_df = df.copy()
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered_df = filtered_df[
        (filtered_df["usage_hour"].dt.date >= start_date)
        & (filtered_df["usage_hour"].dt.date <= end_date)
    ]

filtered_df = apply_excel_multiselect_filter(
    filtered_df, "business_group", "Business Group", st.sidebar
)
filtered_df = apply_excel_multiselect_filter(
    filtered_df, "region", "Region", st.sidebar
)

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()


# ----------------------------
# Shared calculations (match Excel pivots exactly)
# ----------------------------
line_item_pivot = pd.pivot_table(
    filtered_df,
    values="ondemand_cost",
    index="usage_hour",
    columns="line_item_type",
    aggfunc="sum",
    fill_value=0,
).reset_index().sort_values("usage_hour")

line_item_pivot["Hour"] = line_item_pivot["usage_hour"].dt.strftime("%m/%d/%Y %H:%M")

if "SavingsPlanCoveredUsage" not in line_item_pivot.columns:
    line_item_pivot["SavingsPlanCoveredUsage"] = 0
if "Usage" not in line_item_pivot.columns:
    line_item_pivot["Usage"] = 0

raw_line_item_cols = [
    col for col in line_item_pivot.columns
    if col not in ["usage_hour", "Hour"]
]
line_item_pivot["Grand Total"] = line_item_pivot[raw_line_item_cols].sum(axis=1)

# Keep only complete hours in Overview
line_item_pivot = line_item_pivot[line_item_pivot["Grand Total"] > 6000].copy()

line_item_pivot["Coverage %"] = np.where(
    line_item_pivot["Grand Total"] > 0,
    line_item_pivot["SavingsPlanCoveredUsage"] / line_item_pivot["Grand Total"] * 100,
    0,
)

covered_total = line_item_pivot["SavingsPlanCoveredUsage"].sum()
on_demand_total = line_item_pivot["Usage"].sum()
grand_total = line_item_pivot["Grand Total"].sum()
coverage_pct = (covered_total / grand_total * 100) if grand_total > 0 else 0
avg_hourly_on_demand = line_item_pivot["Usage"].mean()

bg_pivot = pd.pivot_table(
    filtered_df,
    values="ondemand_cost",
    index="usage_hour",
    columns="business_group",
    aggfunc="sum",
    fill_value=0,
).reset_index().sort_values("usage_hour")

bg_pivot["Hour"] = bg_pivot["usage_hour"].dt.strftime("%m/%d/%Y %H:%M")

bg_totals = (
    filtered_df.groupby("business_group", dropna=False)["ondemand_cost"]
    .sum()
    .sort_values(ascending=False)
)
ordered_bg_cols = [col for col in bg_totals.index.tolist() if col in bg_pivot.columns]
bg_pivot["Total Spend"] = bg_pivot[ordered_bg_cols].sum(axis=1) if ordered_bg_cols else 0

uncovered_df = filtered_df[filtered_df["line_item_type"] == "Usage"].copy()

instance_table = (
    filtered_df.groupby("instance_type", dropna=False)
    .agg(
        total_spend=("ondemand_cost", "sum"),
        covered_spend=("covered_cost_proxy", "sum"),
        uncovered_spend=("uncovered_cost_proxy", "sum"),
    )
    .reset_index()
    .sort_values("total_spend", ascending=False)
)

opp_table = (
    uncovered_df.groupby(["business_group", "instance_type", "region"], dropna=False)
    .agg(
        uncovered_spend=("ondemand_cost", "sum"),
        usage_amount=("usage_amount", "sum"),
    )
    .reset_index()
    .sort_values("uncovered_spend", ascending=False)
)

bg_coverage = (
    filtered_df.groupby(["business_group", "line_item_type"], dropna=False)["ondemand_cost"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)

if "SavingsPlanCoveredUsage" not in bg_coverage.columns:
    bg_coverage["SavingsPlanCoveredUsage"] = 0
if "Usage" not in bg_coverage.columns:
    bg_coverage["Usage"] = 0

bg_coverage = bg_coverage.rename(
    columns={
        "SavingsPlanCoveredUsage": "SP Covered Spend",
        "Usage": "On-Demand Spend",
    }
)

bg_coverage["Total Spend"] = (
    bg_coverage.drop(columns=["business_group"], errors="ignore").sum(axis=1)
)

bg_coverage["Coverage %"] = np.where(
    bg_coverage["Total Spend"] > 0,
    bg_coverage["SP Covered Spend"] / bg_coverage["Total Spend"] * 100,
    0,
)


def bg_recommendation(row):
    on_demand = row["On-Demand Spend"]
    coverage = row["Coverage %"]
    total_spend = row["Total Spend"]

    if total_spend < 500:
        return "Low spend, lower priority"
    elif coverage < 50 and on_demand >= 1000:
        return "Strong candidate for SP review"
    elif coverage < 75 and on_demand >= 500:
        return "Monitor for purchase opportunity"
    elif coverage >= 90:
        return "Well covered today"
    else:
        return "Review usage trend"


bg_coverage["Recommendation"] = bg_coverage.apply(bg_recommendation, axis=1)
bg_coverage = bg_coverage.sort_values("On-Demand Spend", ascending=False).reset_index(drop=True)


# ----------------------------
# Executive summary
# ----------------------------
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">Executive Summary</div>', unsafe_allow_html=True)

filtered_date_range = format_filtered_date_range(filtered_df)
st.markdown(
    f"""
    <div style="
        background: linear-gradient(180deg, #eef4ff 0%, #f7faff 100%);
        border: 1px solid #d8e5f7;
        border-radius: 14px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.03);
    ">
        <div style="font-size:0.78rem;font-weight:700;color:#597493;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:0.2rem;">Date Range</div>
        <div style="font-size:1rem;font-weight:700;color:#0b1f3a;">{filtered_date_range}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("SP Covered Spend", format_currency(covered_total))
k2.metric("On-Demand Spend", format_currency(on_demand_total))
k3.metric("Coverage %", format_percent(coverage_pct))
k4.metric(
    "Avg Hourly On-Demand",
    format_currency(avg_hourly_on_demand if pd.notnull(avg_hourly_on_demand) else 0),
)

primary_bg = opp_table.iloc[0]["business_group"] if not opp_table.empty else "N/A"
primary_instance = opp_table.iloc[0]["instance_type"] if not opp_table.empty else "N/A"
primary_region = opp_table.iloc[0]["region"] if not opp_table.empty else "N/A"
top_uncovered = opp_table.iloc[0]["uncovered_spend"] if not opp_table.empty else 0

ins1, ins2, ins3 = st.columns(3)
ins1.markdown(
    f"""
    <div class="insight-card">
        <div class="insight-title">Top uncovered area</div>
        <div class="insight-value">{format_currency(top_uncovered)}</div>
        <div class="insight-text">Largest uncovered combination in the filtered dataset, useful for immediate FinOps follow-up.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
ins2.markdown(
    f"""
    <div class="insight-card">
        <div class="insight-title">Primary business group</div>
        <div class="insight-value">{primary_bg}</div>
        <div class="insight-text">Business group currently driving the top uncovered opportunity.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
ins3.markdown(
    f"""
    <div class="insight-card">
        <div class="insight-title">Focus target</div>
        <div class="insight-value">{primary_instance}</div>
        <div class="insight-text">Top instance type in <b>{primary_region}</b> based on uncovered spend opportunity.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Tabs
# ----------------------------
tab_overview, tab_business, tab_opportunities, tab_inventory, tab_bg_coverage = st.tabs(
    [
        "Overview",
        "Business Groups",
        "Opportunities",
        "Inventory",
        "Business Group Coverage",
    ]
)

with tab_overview:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Overview</div>', unsafe_allow_html=True)

    left, right = st.columns(2)

    with left:
        fig_overview_sp = px.line(
            line_item_pivot,
            x="usage_hour",
            y=["SavingsPlanCoveredUsage", "Usage", "Grand Total"],
            title="Coverage",
        )
        fig_overview_sp.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis_tickformat=",.0f",
            yaxis_title="Amount",
            legend_title_text="Legend",
        )
        fig_overview_sp.update_xaxes(title_text="Hour")
        st.plotly_chart(
            fig_overview_sp,
            use_container_width=True,
            key="overview_sp_trend_chart",
        )

    with right:
        fig_overview_cov = px.line(
            line_item_pivot,
            x="usage_hour",
            y="Coverage %",
            title="Hourly Coverage %",
        )
        fig_overview_cov.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(range=[0, 100], ticksuffix="%", tickformat=",.0f"),
        )
        fig_overview_cov.update_xaxes(title_text="Hour")
        st.plotly_chart(
            fig_overview_cov,
            use_container_width=True,
            key="overview_coverage_pct_chart",
        )

    st.markdown("#### Coverage Table")

    # Show only the most recent 14 days by hour in the coverage table
    latest_usage_hour = line_item_pivot["usage_hour"].max()
    coverage_table_cutoff = latest_usage_hour - pd.Timedelta(days=14)

    raw_sp_display = line_item_pivot[
        line_item_pivot["usage_hour"] >= coverage_table_cutoff
    ][["Hour", "SavingsPlanCoveredUsage", "Usage", "Grand Total", "Coverage %"]].copy()

    raw_sp_display = raw_sp_display.sort_values("Hour", ascending=False)

    raw_sp_display["SavingsPlanCoveredUsage"] = raw_sp_display["SavingsPlanCoveredUsage"].apply(format_currency)
    raw_sp_display["Usage"] = raw_sp_display["Usage"].apply(format_currency)
    raw_sp_display["Grand Total"] = raw_sp_display["Grand Total"].apply(format_currency)
    raw_sp_display["Coverage %"] = raw_sp_display["Coverage %"].apply(format_percent)

    st.dataframe(raw_sp_display, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab_business:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Business Groups</div>', unsafe_allow_html=True)

    latest_bg_hour = bg_pivot["usage_hour"].max()
    bg_cutoff = latest_bg_hour - pd.Timedelta(days=14)
    bg_recent = bg_pivot[bg_pivot["usage_hour"] >= bg_cutoff].copy()

    bg_table = bg_recent.drop(columns=["usage_hour"]).copy()
    bg_cols = ["Hour"] + ordered_bg_cols
    if "Total Spend" in bg_table.columns:
        bg_cols += ["Total Spend"]

    bg_table = bg_table[bg_cols]

    for col in bg_table.columns:
        if col != "Hour":
            bg_table[col] = bg_table[col].apply(format_currency)

    st.dataframe(bg_table.head(300), use_container_width=True)

    if ordered_bg_cols:
        fig_business_bg = px.line(
            bg_recent,
            x="usage_hour",
            y=ordered_bg_cols,
            title="Hourly On-Demand Cost by Business Group",
        )
        fig_business_bg.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis_tickformat=",.0f",
            legend_title_text="Legend",
        )
        fig_business_bg.update_xaxes(title_text="Hour")
        st.plotly_chart(
            fig_business_bg,
            use_container_width=True,
            key="business_groups_spend_chart",
        )

    bg_compare = bg_coverage[bg_coverage["Total Spend"] > 25000].copy()

    if not bg_compare.empty:
        bg_compare = bg_compare.sort_values("Total Spend", ascending=False)

        fig_bg_compare = px.bar(
            bg_compare,
            x="business_group",
            y=["SP Covered Spend", "On-Demand Spend"],
            barmode="stack",
            title="Covered vs Uncovered Spend by Business Group",
            labels={
                "business_group": "Business Group",
                "value": "Amount",
                "variable": "Legend",
            },
        )
        fig_bg_compare.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis_tickformat=",.0f",
            legend_title_text="Legend",
            xaxis={"categoryorder": "array", "categoryarray": bg_compare["business_group"].tolist()},
        )
        st.plotly_chart(
            fig_bg_compare,
            use_container_width=True,
            key="bg_compare_chart",
        )

    st.markdown("</div>", unsafe_allow_html=True)

with tab_opportunities:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Opportunities</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Derived analysis view for uncovered spend and optimization follow-up.</div>',
        unsafe_allow_html=True,
    )

    opp_combined_table = (
        uncovered_df.groupby(
            ["business_group", "product_name", "operatng_system", "instance_type", "region"],
            dropna=False,
        )
        .agg(
            uncovered_spend=("ondemand_cost", "sum"),
            usage_amount=("usage_amount", "sum"),
        )
        .reset_index()
        .sort_values("uncovered_spend", ascending=False)
    )

    opp_combined_display = opp_combined_table.head(25).copy()
    opp_combined_display = opp_combined_display.rename(
        columns={
            "business_group": "Business Group",
            "product_name": "Service",
            "operatng_system": "Operating System",
            "instance_type": "Instance Type",
            "region": "Region",
            "uncovered_spend": "Uncovered Spend",
            "usage_amount": "Usage Amount",
        }
    )
    opp_combined_display["Uncovered Spend"] = opp_combined_display["Uncovered Spend"].apply(format_currency)
    opp_combined_display["Usage Amount"] = opp_combined_display["Usage Amount"].apply(format_number)

    st.markdown("#### Opportunities Dashboard")
    st.dataframe(opp_combined_display, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        instance_opp = (
            uncovered_df.groupby("instance_type", dropna=False)["ondemand_cost"]
            .sum()
            .reset_index()
            .sort_values("ondemand_cost", ascending=False)
            .head(15)
        )
        fig_opp_instance = px.bar(
            instance_opp,
            x="instance_type",
            y="ondemand_cost",
            title="Top 15 Uncovered Instance Types",
        )
        fig_opp_instance.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis_tickformat=",.0f")
        st.plotly_chart(
            fig_opp_instance,
            use_container_width=True,
            key="opportunities_instance_chart",
        )

    with col2:
        bg_uncovered = (
            uncovered_df.groupby("business_group", dropna=False)["ondemand_cost"]
            .sum()
            .reset_index()
            .sort_values("ondemand_cost", ascending=False)
        )
        fig_opp_bg = px.bar(
            bg_uncovered,
            x="business_group",
            y="ondemand_cost",
            title="Uncovered Spend by Business Group",
        )
        fig_opp_bg.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis_tickformat=",.0f")
        st.plotly_chart(
            fig_opp_bg,
            use_container_width=True,
            key="opportunities_bg_chart",
        )

    col3, col4 = st.columns(2)

    with col3:
        region_uncovered = (
            uncovered_df.groupby("region", dropna=False)["ondemand_cost"]
            .sum()
            .reset_index()
            .sort_values("ondemand_cost", ascending=False)
        )
        fig_opp_region = px.bar(
            region_uncovered,
            x="region",
            y="ondemand_cost",
            title="Uncovered Spend by Region",
        )
        fig_opp_region.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis_tickformat=",.0f")
        st.plotly_chart(
            fig_opp_region,
            use_container_width=True,
            key="opportunities_region_chart",
        )

    with col4:
        instance_compare = instance_table.head(15).copy()
        fig_opp_compare = px.bar(
            instance_compare,
            x="instance_type",
            y=["covered_spend", "uncovered_spend"],
            barmode="stack",
            title="Covered vs Uncovered Spend by Instance Type",
        )
        fig_opp_compare.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis_tickformat=",.0f",
            legend_title_text="Legend",
        )
        st.plotly_chart(
            fig_opp_compare,
            use_container_width=True,
            key="opportunities_instance_compare_chart",
        )

    heat_df = (
        uncovered_df.groupby(["date", "hour_of_day"])["ondemand_cost"]
        .sum()
        .reset_index()
    )
    if not heat_df.empty:
        fig_opp_heat = px.density_heatmap(
            heat_df,
            x="hour_of_day",
            y="date",
            z="ondemand_cost",
            title="Uncovered Spend by Day and Hour",
        )
        fig_opp_heat.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            coloraxis_colorbar_tickformat=",.0f",
        )
        st.plotly_chart(
            fig_opp_heat,
            use_container_width=True,
            key="opportunities_heatmap_chart",
        )

    st.markdown("</div>", unsafe_allow_html=True)

with tab_inventory:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Inventory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Derived inventory summary for Savings Plan ARNs and remaining term.</div>',
        unsafe_allow_html=True,
    )

    inventory_df = filtered_df[filtered_df["is_sp_covered"]].copy()

    if not inventory_df.empty:
        inventory_table = (
            inventory_df.groupby(
                [
                    "savings_plan_arn",
                    "savings_plan_start_date",
                    "savings_plan_end_date",
                    "savings_plan_payment_option",
                    "savings_plan_purchase_term",
                ],
                dropna=False,
            )
            .agg(
                covered_spend=("ondemand_cost", "sum"),
                usage_amount=("usage_amount", "sum"),
            )
            .reset_index()
            .sort_values("covered_spend", ascending=False)
        )

        today_utc = pd.Timestamp.now(tz="UTC").normalize()
        inventory_table["days_remaining"] = (
            inventory_table["savings_plan_end_date"] - today_utc
        ).dt.days

        inventory_display = inventory_table.copy()
        inventory_display["savings_plan_start_date"] = inventory_display["savings_plan_start_date"].dt.strftime("%m/%d/%Y")
        inventory_display["savings_plan_end_date"] = inventory_display["savings_plan_end_date"].dt.strftime("%m/%d/%Y")
        inventory_display["covered_spend"] = inventory_display["covered_spend"].apply(format_currency)
        inventory_display["usage_amount"] = inventory_display["usage_amount"].apply(format_number)
        inventory_display["days_remaining"] = inventory_display["days_remaining"].fillna(0).round(0).astype(int)

        st.dataframe(inventory_display.head(200), use_container_width=True)
    else:
        st.info("No Savings Plan inventory rows were identified from the current filters.")

    st.markdown("</div>", unsafe_allow_html=True)

with tab_bg_coverage:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Business Group Coverage</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Derived summary for directional Savings Plan review. This tab is color-coded by recommendation.</div>',
        unsafe_allow_html=True,
    )

    bg_coverage_display = bg_coverage[
        ["business_group", "SP Covered Spend", "On-Demand Spend", "Total Spend", "Coverage %", "Recommendation"]
    ].copy()
    bg_coverage_display["SP Covered Spend"] = bg_coverage_display["SP Covered Spend"].apply(format_currency)
    bg_coverage_display["On-Demand Spend"] = bg_coverage_display["On-Demand Spend"].apply(format_currency)
    bg_coverage_display["Total Spend"] = bg_coverage_display["Total Spend"].apply(format_currency)
    bg_coverage_display["Coverage %"] = bg_coverage_display["Coverage %"].apply(format_percent)

    styled_bg_coverage = bg_coverage_display.style.apply(
        highlight_row,
        axis=1,
    )
    st.dataframe(styled_bg_coverage, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        fig_bg_cov_pct = px.bar(
            bg_coverage.sort_values("Coverage %", ascending=False),
            x="business_group",
            y="Coverage %",
            color="Recommendation",
            color_discrete_map=recommendation_color_map,
            title="Coverage % by Business Group",
        )
        fig_bg_cov_pct.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(range=[0, 100], ticksuffix="%", tickformat=",.0f"),
        )
        st.plotly_chart(
            fig_bg_cov_pct,
            use_container_width=True,
            key="bg_coverage_pct_chart",
        )

    with c2:
        bg_spend_long = bg_coverage.melt(
            id_vars=["business_group", "Recommendation"],
            value_vars=["SP Covered Spend", "On-Demand Spend"],
            var_name="Spend Type",
            value_name="Amount",
        )

        fig_bg_cov_spend = px.bar(
            bg_spend_long,
            x="business_group",
            y="Amount",
            color="Recommendation",
            pattern_shape="Spend Type",
            color_discrete_map=recommendation_color_map,
            title="Covered vs On-Demand Spend by Business Group",
        )
        fig_bg_cov_spend.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis_tickformat=",.0f")
        st.plotly_chart(
            fig_bg_cov_spend,
            use_container_width=True,
            key="bg_coverage_spend_chart",
        )

    st.markdown("</div>", unsafe_allow_html=True)
