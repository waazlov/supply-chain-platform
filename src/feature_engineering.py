"""Feature engineering for analytical and predictive datasets."""

from __future__ import annotations

import pandas as pd


def add_shipment_features(shipments: pd.DataFrame) -> pd.DataFrame:
    """Create derived shipment features without using post-delivery leakage fields."""
    df = shipments.copy()
    for column in ["order_date", "ship_date", "expected_delivery_date", "actual_delivery_date"]:
        df[column] = pd.to_datetime(df[column])
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    df["order_week"] = df["order_date"].dt.to_period("W").astype(str)
    df["order_day_of_week"] = df["order_date"].dt.dayofweek
    df["expected_transit_days"] = (df["expected_delivery_date"] - df["ship_date"]).dt.days
    df["actual_transit_days"] = (df["actual_delivery_date"] - df["ship_date"]).dt.days
    df["delay_days"] = (df["actual_delivery_date"] - df["expected_delivery_date"]).dt.days.clip(lower=0)
    df["order_cycle_time_days"] = (df["actual_delivery_date"] - df["order_date"]).dt.days
    df["cost_per_km"] = df["shipping_cost"] / df["distance_km"].clip(lower=1)
    df["cost_per_unit"] = df["shipping_cost"] / df["quantity"].clip(lower=1)
    df["inventory_gap"] = df["inventory_level"] - df["reorder_point"]
    df["delay_cost_estimate"] = (
        df["delay_days"] * (12 + 0.015 * df["quantity"] * df["unit_price"]) * (1 + df["priority_level"].map({"Standard": 0, "Expedited": 0.4, "Critical": 0.9}))
    ).round(2)
    df["stockout_cost_estimate"] = (df["stockout_flag"] * df["quantity"] * df["unit_price"] * 0.22).round(2)
    return df


def build_model_frame(shipments: pd.DataFrame, products: pd.DataFrame, suppliers: pd.DataFrame, routes: pd.DataFrame) -> pd.DataFrame:
    """Join feature tables for late-delivery modeling."""
    df = add_shipment_features(shipments)
    df = df.merge(products[["product_id", "product_category", "intermittent_demand_flag"]], on="product_id", how="left")
    df = df.merge(suppliers[["supplier_id", "reliability_score"]], on="supplier_id", how="left")
    df = df.merge(routes[["route_id", "route_capacity_per_week"]], on="route_id", how="left")
    return df

