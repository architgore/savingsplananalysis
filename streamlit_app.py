import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="AWS Savings Plan Dashboard", layout="wide")

st.title("AWS Savings Plan Dashboard")
st.caption("Upload AWS_Data.csv to analyze coverage, spend, and Savings Plan trends.")

REQUIRED_COLUMNS = [
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
]


def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        st.stop()

    df["usage_hour"] = pd.to_datetime(df["usage_hour"], errors="coerce")
    df["savings_plan_start_date"] = pd.to_datetime(df["savings_plan_start_date"], errors="coerce")
    df["savings_plan_end_date"] = pd.to_datetime(df["savings_plan_end_date"], errors="coerce")

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

    df["date"] = df["usage_hour"].dt.date
    df["month"] = df["usage_hour"].dt.to_period("M").astype(str)

    # Heuristic: rows with a Savings Plan ARN are treated as SP-covered rows.
    df["is_sp_covered"] = (
        df["savings_plan_arn"].notna()
        & (df["savings_plan_arn"].astype(str).str.strip() != "")
        & (df["savings_plan_arn"] != "Unknown")
    )

    df["sp_covered_cost"] = np.where(df["is_sp_covered"], df["net_fiscal_cost"], 0)
    df["on_demand_cost_only"] = np.where(~df["is_sp_covered"], df["ondemand_cost"], 0)
    df["total_candidate_spend"] = df["sp_covered_cost"] + df["on_demand_cost_only"]

    return df


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    min_date = df["usage_hour"].min().date() if df["usage_hour"].notna().any() else None
    max_date = df["usage_hour"].max().date() if df["usage_hour"].notna().any() else None

    if min_date and max_date:
        date_range = st.sidebar.date_input(
            "Usage date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df["usage_hour"].dt.date >= start_date) & (df["usage_hour"].dt.date <= end_date)]

    payer_accounts = sorted(df["payer_account_id"].dropna().unique().tolist())
    selected_payers = st.sidebar.multiselect("Payer Account", payer_accounts, default=payer_accounts)
    if selected_payers:
        df = df[df["payer_account_id"].isin(selected_payers)]

    business_groups = sorted(df["business_group"].dropna().unique().tolist())
    selected_bgs = st.sidebar.multiselect("Business Group", business_groups, default=business_groups)
    if selected_bgs:
        df = df[df["business_group"].isin(selected_bgs)]

    products = sorted(df["product_code"].dropna().unique().tolist())
    selected_products = st.sidebar.multiselect("Product Code", products, default=products)
    if selected_products:
        df = df[df["product_code"].isin(selected_products)]

    regions = sorted(df["region"].dropna().unique().tolist())
    selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
    if selected_regions:
        df = df[df["region"].isin(selected_regions)]

    operating_systems = sorted(df["operatng_system"].dropna().unique().tolist())
    selected_os = st.sidebar.multiselect("Operating System", operating_systems, default=operating_systems)
    if selected_os:
        df = df[df["operatng_system"].isin(selected_os)]

    instance_types = sorted(df["instance_type"].dropna().unique().tolist())
    selected_instances = st.sidebar.multiselect("Instance Type", instance_types, default=instance_types)
    if selected_instances:
        df = df[df["instance_type"].isin(selected_instances)]

    return df


def create_kpis(df: pd.DataFrame):
    total_net_cost = df["net_fiscal_cost"].sum()
    total_od_cost = df["ondemand_cost"].sum()
    sp_covered_cost = df["sp_covered_cost"].sum()
    total_candidate_spend = df["total_candidate_spend"].sum()
    coverage_pct = (sp_covered_cost / total_candidate_spend * 100) if total_candidate_spend > 0 else 0
    total_usage = df["usage_amount"].sum()
    uncovered_spend = df["on_demand_cost_only"].sum()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Net Fiscal Cost", f"${total_net_cost:,.2f}")
    c2.metric("On-Demand Cost", f"${total_od_cost:,.2f}")
    c3.metric("SP Covered Spend", f"${sp_covered_cost:,.2f}")
    c4.metric("Coverage %", f"{coverage_pct:,.1f}%")
    c5.metric("Uncovered Spend", f"${uncovered_spend:,.2f}")
    c6.metric("Usage Amount", f"{total_usage:,.2f}")


def coverage_vs_usage_dashboard(df: pd.DataFrame):
    st.subheader("Savings Plan Coverage vs Usage")

    daily = (
        df.groupby("date", dropna=False)
        .agg(
            usage_amount=("usage_amount", "sum"),
            sp_covered_cost=("sp_covered_cost", "sum"),
            on_demand_cost_only=("on_demand_cost_only", "sum"),
            net_fiscal_cost=("net_fiscal_cost", "sum"),
        )
        .reset_index()
    )
    daily["coverage_pct"] = np.where(
        (daily["sp_covered_cost"] + daily["on_demand_cost_only"]) > 0,
        daily["sp_covered_cost"] / (daily["sp_covered_cost"] + daily["on_demand_cost_only"]) * 100,
        0,
    )

    chart_metric = st.radio(
        "View coverage alongside",
        ["Usage Amount", "On-Demand Cost", "Net Fiscal Cost"],
        horizontal=True,
    )

    if chart_metric == "Usage Amount":
        y_col = "usage_amount"
        y_label = "Usage Amount"
    elif chart_metric == "On-Demand Cost":
        y_col = "on_demand_cost_only"
        y_label = "On-Demand Cost"
    else:
        y_col = "net_fiscal_cost"
        y_label = "Net Fiscal Cost"

    fig = px.line(
        daily,
        x="date",
        y=["sp_covered_cost", y_col],
        markers=True,
        title=f"SP Covered Spend vs {y_label} by Day",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(daily, use_container_width=True)


def coverage_percent_dashboard(df: pd.DataFrame):
    st.subheader("Coverage % Dashboard")

    by_bg = (
        df.groupby("business_group", dropna=False)
        .agg(
            sp_covered_cost=("sp_covered_cost", "sum"),
            on_demand_cost_only=("on_demand_cost_only", "sum"),
            net_fiscal_cost=("net_fiscal_cost", "sum"),
        )
        .reset_index()
    )
    by_bg["coverage_pct"] = np.where(
        (by_bg["sp_covered_cost"] + by_bg["on_demand_cost_only"]) > 0,
        by_bg["sp_covered_cost"] / (by_bg["sp_covered_cost"] + by_bg["on_demand_cost_only"]) * 100,
        0,
    )
    by_bg = by_bg.sort_values("coverage_pct", ascending=False)

    fig = px.bar(
        by_bg,
        x="business_group",
        y="coverage_pct",
        title="Coverage % by Business Group",
        hover_data=["sp_covered_cost", "on_demand_cost_only", "net_fiscal_cost"],
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(by_bg, use_container_width=True)

    by_day = (
        df.groupby("date", dropna=False)
        .agg(
            sp_covered_cost=("sp_covered_cost", "sum"),
            on_demand_cost_only=("on_demand_cost_only", "sum"),
        )
        .reset_index()
    )
    by_day["coverage_pct"] = np.where(
        (by_day["sp_covered_cost"] + by_day["on_demand_cost_only"]) > 0,
        by_day["sp_covered_cost"] / (by_day["sp_covered_cost"] + by_day["on_demand_cost_only"]) * 100,
        0,
    )

    fig_day = px.line(
        by_day,
        x="date",
        y="coverage_pct",
        markers=True,
        title="Daily Coverage % Trend",
    )
    st.plotly_chart(fig_day, use_container_width=True)


def business_group_spend_dashboard(df: pd.DataFrame):
    st.subheader("Business Group Spend Dashboard")

    spend_bg = (
        df.groupby("business_group", dropna=False)
        .agg(
            net_fiscal_cost=("net_fiscal_cost", "sum"),
            ondemand_cost=("ondemand_cost", "sum"),
            usage_amount=("usage_amount", "sum"),
        )
        .reset_index()
        .sort_values("net_fiscal_cost", ascending=False)
    )

    fig = px.bar(
        spend_bg,
        x="business_group",
        y="net_fiscal_cost",
        title="Net Fiscal Cost by Business Group",
        hover_data=["ondemand_cost", "usage_amount"],
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(spend_bg, use_container_width=True)


def additional_sp_analysis_dashboards(df: pd.DataFrame):
    st.subheader("Additional Savings Plan Analysis Views")

    col1, col2 = st.columns(2)

    with col1:
        by_instance = (
            df.groupby("instance_type", dropna=False)
            .agg(
                net_fiscal_cost=("net_fiscal_cost", "sum"),
                sp_covered_cost=("sp_covered_cost", "sum"),
                on_demand_cost_only=("on_demand_cost_only", "sum"),
            )
            .reset_index()
            .sort_values("net_fiscal_cost", ascending=False)
            .head(15)
        )
        fig_instance = px.bar(
            by_instance,
            x="instance_type",
            y=["sp_covered_cost", "on_demand_cost_only"],
            title="Top 15 Instance Types by Covered vs Uncovered Spend",
            barmode="stack",
        )
        st.plotly_chart(fig_instance, use_container_width=True)

    with col2:
        by_region = (
            df.groupby("region", dropna=False)
            .agg(
                net_fiscal_cost=("net_fiscal_cost", "sum"),
                sp_covered_cost=("sp_covered_cost", "sum"),
                on_demand_cost_only=("on_demand_cost_only", "sum"),
            )
            .reset_index()
            .sort_values("net_fiscal_cost", ascending=False)
        )
        fig_region = px.bar(
            by_region,
            x="region",
            y=["sp_covered_cost", "on_demand_cost_only"],
            title="Covered vs Uncovered Spend by Region",
            barmode="stack",
        )
        st.plotly_chart(fig_region, use_container_width=True)

    sp_inventory = (
        df[df["is_sp_covered"]]
        .groupby(
            [
                "savings_plan_arn",
                "savings_plan_payment_option",
                "savings_plan_purchase_term",
                "savings_plan_start_date",
                "savings_plan_end_date",
            ],
            dropna=False,
        )
        .agg(
            covered_spend=("sp_covered_cost", "sum"),
            usage_amount=("usage_amount", "sum"),
        )
        .reset_index()
        .sort_values("covered_spend", ascending=False)
    )

    st.markdown("### Savings Plan Inventory")
    st.dataframe(sp_inventory, use_container_width=True)

    uncovered = (
        df[~df["is_sp_covered"]]
        .groupby(["business_group", "usage_account_id", "instance_type", "region"], dropna=False)
        .agg(
            uncovered_spend=("ondemand_cost", "sum"),
            usage_amount=("usage_amount", "sum"),
        )
        .reset_index()
        .sort_values("uncovered_spend", ascending=False)
        .head(25)
    )

    st.markdown("### Top Uncovered Spend Opportunities")
    st.dataframe(uncovered, use_container_width=True)


def main():
    uploaded_file = st.file_uploader("Upload AWS_Data CSV", type=["csv"])

    st.markdown("Or place **AWS_Data.csv** in the same folder as this script and use the local file option below.")
    use_local_file = st.checkbox("Use local AWS_Data.csv from script folder")

    file_source = None

    if uploaded_file is not None:
        file_source = uploaded_file
    elif use_local_file:
        local_file_name = "AWS_Data.csv"
        try:
            file_source = local_file_name
            pd.read_csv(local_file_name, nrows=1)
        except FileNotFoundError:
            st.error("AWS_Data.csv was not found in the same folder as the script.")
            st.stop()
        except Exception as e:
            st.error(f"Unable to read local AWS_Data.csv: {e}")
            st.stop()

    if file_source is None:
        st.warning("Please upload AWS_Data.csv or check the local file option.")
        st.stop()

    df = load_data(file_source)
    filtered_df = apply_filters(df)

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        st.stop()

    create_kpis(filtered_df)
    st.divider()
    coverage_vs_usage_dashboard(filtered_df)
    st.divider()
    coverage_percent_dashboard(filtered_df)
    st.divider()
    business_group_spend_dashboard(filtered_df)
    st.divider()
    additional_sp_analysis_dashboards(filtered_df)


if __name__ == "__main__":
    main()
