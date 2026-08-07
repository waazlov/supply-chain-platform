"""Cleaning routines for raw supply chain tables."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.validation import APPROVED


def clean_tables(tables: dict[str, pd.DataFrame], config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Clean duplicate, missing, invalid, and extreme shipment records."""
    cleaned = {name: table.copy() for name, table in tables.items()}
    shipments = cleaned["shipments"].copy()
    shipments = shipments.drop_duplicates("shipment_id", keep="first")
    shipments["carrier"] = shipments["carrier"].fillna("Unknown")
    shipments.loc[~shipments["transport_mode"].isin(APPROVED["transport_mode"]), "transport_mode"] = "Truck"
    for column in ["order_date", "ship_date", "expected_delivery_date", "actual_delivery_date"]:
        shipments[column] = pd.to_datetime(shipments[column], errors="coerce")
    invalid = (
        shipments["shipment_id"].isna()
        | shipments["order_id"].isna()
        | (shipments["quantity"] <= 0)
        | (shipments["shipping_cost"] < 0)
        | (shipments["fuel_cost"] < 0)
        | (shipments["ship_date"] < shipments["order_date"])
        | (shipments["actual_delivery_date"] < shipments["ship_date"])
    )
    shipments = shipments.loc[~invalid].copy()
    for score in ["weather_severity", "route_congestion_score"]:
        shipments[score] = shipments[score].clip(0, 1)
    cutoff = shipments["shipping_cost"].quantile(config["validation"]["shipping_cost_outlier_quantile"])
    shipments["shipping_cost_outlier_flag"] = (shipments["shipping_cost"] > cutoff).astype(int)
    shipments["shipping_cost"] = np.minimum(shipments["shipping_cost"], cutoff).round(2)
    shipments["late_delivery_flag"] = (
        shipments["actual_delivery_date"] > shipments["expected_delivery_date"]
    ).astype(int)
    shipments["shipment_status"] = np.where(shipments["late_delivery_flag"].eq(1), "Delivered Late", "Delivered On Time")
    shipments.loc[shipments["stockout_flag"].eq(1) & (shipments["inventory_level"] < shipments["quantity"]), "shipment_status"] = "Backordered"
    date_columns = ["order_date", "ship_date", "expected_delivery_date", "actual_delivery_date"]
    for column in date_columns:
        shipments[column] = shipments[column].dt.strftime("%Y-%m-%d")
    cleaned["shipments"] = shipments.reset_index(drop=True)
    return cleaned

