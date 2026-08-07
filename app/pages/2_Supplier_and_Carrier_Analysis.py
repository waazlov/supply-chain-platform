"""Supplier and carrier performance page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from app.dashboard_utils import load_csv, require_data


st.title("Supplier and Carrier Analysis")
suppliers = load_csv("supplier_scorecard.csv")
carriers = load_csv("carrier_performance_scorecard.csv")
if require_data(suppliers, carriers):
    c1, c2 = st.columns(2)
    with c1:
        top = suppliers.sort_values("supplier_risk_score", ascending=False).head(15)
        st.plotly_chart(px.bar(top, x="supplier_id", y="supplier_risk_score", color="supplier_defect_rate", title="Supplier Risk Scorecard"), width="stretch")
    with c2:
        st.plotly_chart(px.scatter(carriers, x="average_shipping_cost", y="on_time_delivery_rate", size="shipment_count", color="transport_mode", hover_name="carrier", title="Carrier Cost Versus Reliability"), width="stretch")
    st.dataframe(suppliers.sort_values("supplier_risk_score", ascending=False), width="stretch")
    st.subheader("Insight")
    st.write("Supplier performance combines defect rate, lead time, service reliability, and stockout exposure. Carrier analysis compares delivery reliability with cost, rather than ranking on price alone.")
