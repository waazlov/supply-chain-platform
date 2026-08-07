"""Main Streamlit dashboard entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dashboard_utils import apply_sidebar_filters, kpi, load_csv, require_data

st.set_page_config(page_title="Supply Chain Intelligence", layout="wide")
st.title("Supply Chain Intelligence and Optimization Platform")

kpis = load_csv("executive_kpi_summary.csv")
monthly = load_csv("monthly_logistics_cost_summary.csv")
performance = load_csv("shipment_performance_summary.csv")
quality = load_csv("data_quality_summary.csv")

if require_data(kpis, monthly, performance):
    k = kpis.iloc[0]
    cols = st.columns(5)
    with cols[0]:
        kpi("Shipments", f"{int(k['total_shipments']):,}")
    with cols[1]:
        kpi("On-time rate", f"{k['on_time_delivery_rate']:.1%}")
    with cols[2]:
        kpi("Avg delay", f"{k['average_delay_days']:.2f} days")
    with cols[3]:
        kpi("Logistics cost", f"${k['total_logistics_cost']:,.0f}")
    with cols[4]:
        kpi("Stockout rate", f"{k['stockout_rate']:.1%}")

    filtered = apply_sidebar_filters(performance)
    if filtered.empty:
        st.warning("No records match the selected filters.")
    else:
        left, right = st.columns(2)
        with left:
            st.plotly_chart(px.line(monthly, x="order_month", y="total_shipping_cost", title="Monthly Logistics Cost", markers=True), width="stretch")
        with right:
            trend = filtered.groupby("order_month", as_index=False).agg(on_time_delivery_rate=("on_time_delivery_rate", "mean"))
            st.plotly_chart(px.line(trend, x="order_month", y="on_time_delivery_rate", title="On-Time Delivery Trend", markers=True), width="stretch")
        st.plotly_chart(
            px.bar(
                filtered.groupby("priority_level", as_index=False).agg(estimated_delay_cost=("estimated_delay_cost", "sum")),
                x="priority_level",
                y="estimated_delay_cost",
                title="Estimated Delay Cost by Priority",
            ),
            width="stretch",
        )
        st.subheader("Insight")
        st.write(
            "The executive view connects service reliability, cost, and inventory risk. "
            "Use the filters to isolate categories, modes, carriers, and regions that are contributing most to avoidable financial impact."
        )
    if not quality.empty:
        st.caption(
            f"Data quality: {int(quality.iloc[0]['records_rejected']):,} rejected records and "
            f"{int(quality.iloc[0]['records_corrected']):,} corrected records in the latest run."
        )
