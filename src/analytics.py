"""Python analytical report generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px

from src.feature_engineering import add_shipment_features


def build_eda_report(tables: dict[str, pd.DataFrame], output_dir: Path) -> Path:
    """Create a reproducible HTML exploratory analysis report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    shipments = add_shipment_features(tables["shipments"])
    shipments = shipments.merge(tables["products"][["product_id", "product_category"]], on="product_id", how="left")
    monthly = shipments.groupby("order_month", as_index=False).agg(
        shipments=("shipment_id", "count"),
        late_rate=("late_delivery_flag", "mean"),
        shipping_cost=("shipping_cost", "sum"),
        avg_delay_days=("delay_days", "mean"),
    )
    supplier = shipments.groupby("supplier_id", as_index=False).agg(
        shipments=("shipment_id", "count"),
        late_rate=("late_delivery_flag", "mean"),
        defect_rate=("defect_flag", "mean"),
        avg_lead_time=("supplier_lead_time_days", "mean"),
    ).sort_values(["late_rate", "shipments"], ascending=[False, False]).head(15)
    route = shipments.groupby("route_id", as_index=False).agg(
        shipments=("shipment_id", "count"),
        avg_delay_days=("delay_days", "mean"),
        avg_cost=("shipping_cost", "mean"),
        avg_congestion=("route_congestion_score", "mean"),
    )
    figures = [
        px.line(monthly, x="order_month", y="late_rate", title="Late Delivery Rate Over Time"),
        px.line(monthly, x="order_month", y="shipping_cost", title="Monthly Logistics Cost"),
        px.bar(supplier, x="supplier_id", y="defect_rate", title="Highest Supplier Defect Rates"),
        px.scatter(route, x="avg_cost", y="avg_delay_days", size="shipments", color="avg_congestion", hover_name="route_id", title="Route Cost Versus Delay"),
        px.box(shipments, x="transport_mode", y="delay_days", color="priority_level", title="Delay Distribution by Mode and Priority"),
    ]
    corr_cols = [
        "late_delivery_flag", "distance_km", "shipping_cost", "supplier_lead_time_days",
        "warehouse_processing_hours", "weather_severity", "route_congestion_score", "inventory_gap",
    ]
    correlations = shipments[corr_cols].corr(numeric_only=True)["late_delivery_flag"].sort_values(ascending=False).reset_index()
    html = ["<html><head><meta charset='utf-8'><title>Exploratory Analysis</title>"]
    html.append("<style>body{font-family:Arial,sans-serif;margin:32px;max-width:1200px;} table{border-collapse:collapse;} th,td{border:1px solid #ddd;padding:6px;}</style></head><body>")
    html.append("<h1>Supply Chain Exploratory Analysis</h1>")
    html.append("<p>This report summarizes observed relationships. It supports business interpretation and prediction, but it does not make causal claims.</p>")
    html.append("<h2>Operational Variable Correlations With Late Delivery</h2>")
    html.append(correlations.to_html(index=False))
    for fig in figures:
        html.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    html.append("</body></html>")
    path = output_dir / "exploratory_analysis.html"
    path.write_text("\n".join(html), encoding="utf-8")
    return path
