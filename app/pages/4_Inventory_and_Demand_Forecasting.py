"""Inventory and demand forecasting page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.dashboard_utils import load_csv, require_data


st.title("Inventory and Demand Forecasting")
forecast = load_csv("demand_forecast.csv")
inventory = load_csv("inventory_recommendations.csv")
if require_data(forecast, inventory):
    category = st.selectbox("Product category", sorted(forecast["product_category"].unique().tolist()))
    f = forecast[forecast["product_category"].eq(category)]
    st.plotly_chart(px.line(f, x="week_start", y=["forecast_units", "lower_80", "upper_80"], title="Twelve-Week Demand Forecast"), width="stretch")
    risk = inventory.sort_values("estimated_stockout_risk", ascending=False).head(50)
    st.plotly_chart(px.scatter(risk, x="recommended_order_quantity", y="estimated_stockout_risk", size="potential_weekly_savings", color="policy_status", hover_data=["product_id", "warehouse_id"], title="Inventory Risk Matrix"), width="stretch")
    st.subheader("Insight")
    st.write("Forecasts support inventory policy decisions, while recommendation safeguards flag combinations with limited history so they are not treated as high-confidence automation candidates.")
