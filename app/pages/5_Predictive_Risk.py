"""Predictive late-shipment risk page."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard_utils import load_csv, require_data

st.title("Predictive Risk")
scores = load_csv("late_delivery_scored_shipments.csv")
metrics = load_csv("late_delivery_metrics.csv")
if require_data(scores, metrics):
    st.plotly_chart(px.histogram(scores, x="late_probability", color="priority_level", nbins=40, title="Late Shipment Probability Distribution"), width="stretch")
    by_priority = scores.groupby("priority_level", as_index=False).agg(avg_late_probability=("late_probability", "mean"), actual_late_rate=("late_delivery_flag", "mean"))
    st.plotly_chart(px.bar(by_priority, x="priority_level", y=["avg_late_probability", "actual_late_rate"], barmode="group", title="Risk by Shipment Priority"), width="stretch")
    st.dataframe(metrics, width="stretch")
    st.subheader("Insight")
    st.write("The model is designed for prioritization before delivery. Recall receives extra weight because missing a likely late critical shipment is often more expensive than reviewing a false alert.")
