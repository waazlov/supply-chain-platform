"""Optimization recommendations page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.dashboard_utils import load_csv, require_data


st.title("Optimization Recommendations")
alloc = load_csv("shipment_allocation_optimization.csv")
summary = load_csv("shipment_allocation_optimization_summary.csv")
inventory = load_csv("inventory_recommendations.csv")
if require_data(alloc, summary, inventory):
    s = summary.iloc[0]
    cols = st.columns(3)
    cols[0].metric("Estimated allocation savings", f"${s['estimated_savings']:,.0f}")
    cols[1].metric("Optimized on-time rate", f"{s['expected_on_time_rate_optimized']:.1%}")
    cols[2].metric("Max capacity utilization", f"{s['max_capacity_utilization']:.1%}")
    st.plotly_chart(px.bar(alloc, x="carrier", y=["observed_shipments", "optimized_shipments"], color="transport_mode", barmode="group", title="Current Versus Optimized Allocation"), width="stretch")
    top = inventory.sort_values("potential_weekly_savings", ascending=False).head(20)
    st.plotly_chart(px.bar(top, x="product_id", y="potential_weekly_savings", color="warehouse_id", title="Top Inventory Savings Opportunities"), width="stretch")
    st.subheader("Insight")
    st.write("The allocation model balances cost, capacity, and reliability at an aggregate level. Inventory recommendations quantify the tradeoff between service risk and carrying cost.")
