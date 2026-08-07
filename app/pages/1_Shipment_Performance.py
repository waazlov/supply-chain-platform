"""Shipment performance dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard_utils import apply_sidebar_filters, load_csv, require_data

st.title("Shipment Performance")
df = load_csv("shipment_performance_summary.csv")
if require_data(df):
    filtered = apply_sidebar_filters(df)
    if filtered.empty:
        st.warning("No shipment performance records match the selected filters.")
    else:
        trend = filtered.groupby("order_month", as_index=False).agg(
            on_time_delivery_rate=("on_time_delivery_rate", "mean"),
            average_delay_days=("average_delay_days", "mean"),
            total_shipping_cost=("total_shipping_cost", "sum"),
        )
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.line(trend, x="order_month", y="on_time_delivery_rate", title="On-Time Delivery Rate"), width="stretch")
        with c2:
            st.plotly_chart(px.histogram(filtered, x="average_delay_days", color="priority_level", title="Delay Distribution"), width="stretch")
        st.plotly_chart(px.bar(trend, x="order_month", y="total_shipping_cost", title="Monthly Shipping Cost"), width="stretch")
        st.subheader("Insight")
        st.write("Late deliveries are best evaluated with cost and priority together, because missed critical shipments create larger operational exposure than routine delays.")
