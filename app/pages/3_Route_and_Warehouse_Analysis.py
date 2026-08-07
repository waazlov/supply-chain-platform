"""Route and warehouse analysis page."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard_utils import load_csv, require_data

st.title("Route and Warehouse Analysis")
routes = load_csv("route_performance_summary.csv")
warehouses = load_csv("warehouse_utilization_summary.csv")
if require_data(routes, warehouses):
    st.plotly_chart(px.scatter(routes, x="cost_per_km", y="average_delay_days", color="route_risk_score", size="shipment_count", hover_name="route_id", title="Route Cost Versus Delay"), width="stretch")
    st.plotly_chart(px.bar(warehouses.sort_values("warehouse_processing_time", ascending=False), x="warehouse_id", y="warehouse_processing_time", color="capacity_utilization_ratio", title="Warehouse Processing Time and Utilization"), width="stretch")
    st.subheader("Insight")
    st.write("Routes with both high cost per kilometer and elevated delay days are candidates for contract review, mode changes, or capacity rebalancing. Warehouse processing time highlights congestion risk before shipment transit begins.")
