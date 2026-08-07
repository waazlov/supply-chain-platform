"""Inventory and shipment allocation optimization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.stats import norm


def optimize_inventory(tables: dict[str, pd.DataFrame], config: dict[str, Any], output_dir: Path) -> pd.DataFrame:
    """Calculate safety stock, reorder points, EOQ, and savings estimates."""
    output_dir.mkdir(parents=True, exist_ok=True)
    shipments = tables["shipments"].copy()
    shipments["order_date"] = pd.to_datetime(shipments["order_date"])
    shipments["week_start"] = shipments["order_date"].dt.to_period("W").dt.start_time
    demand = shipments.groupby(["product_id", "warehouse_id", "week_start"], as_index=False).agg(demand_units=("quantity", "sum"))
    stats = demand.groupby(["product_id", "warehouse_id"], as_index=False).agg(
        avg_weekly_demand=("demand_units", "mean"),
        demand_std=("demand_units", "std"),
        weeks_observed=("demand_units", "count"),
    )
    lead = shipments.groupby(["product_id", "warehouse_id"], as_index=False).agg(
        avg_lead_time_days=("supplier_lead_time_days", "mean"),
        lead_time_std_days=("supplier_lead_time_days", "std"),
        current_inventory=("inventory_level", "median"),
        current_reorder_point=("reorder_point", "median"),
        unit_price=("unit_price", "median"),
        current_stockout_rate=("stockout_flag", "mean"),
    )
    rec = stats.merge(lead, on=["product_id", "warehouse_id"], how="left").fillna(0)
    z = float(norm.ppf(config["inventory"]["service_level"]))
    daily_demand = rec["avg_weekly_demand"] / 7
    daily_std = rec["demand_std"].fillna(0) / np.sqrt(7)
    lead_days = rec["avg_lead_time_days"].clip(lower=1)
    rec["safety_stock"] = (z * np.sqrt(lead_days * daily_std**2 + (daily_demand**2) * rec["lead_time_std_days"].fillna(0).clip(lower=0)**2)).round(0)
    rec["reorder_point_recommended"] = (daily_demand * lead_days + rec["safety_stock"]).round(0)
    annual_demand = rec["avg_weekly_demand"] * 52
    holding_cost = rec["unit_price"].clip(lower=1) * float(config["inventory"]["holding_cost_rate"])
    rec["economic_order_quantity"] = np.sqrt(2 * annual_demand * float(config["inventory"]["ordering_cost"]) / holding_cost).round(0)
    rec["recommended_order_quantity"] = np.maximum(0, rec["reorder_point_recommended"] + rec["economic_order_quantity"] - rec["current_inventory"]).round(0)
    rec["estimated_stockout_risk"] = np.maximum(0.01, rec["current_stockout_rate"] * (rec["current_reorder_point"] / rec["reorder_point_recommended"].replace(0, np.nan)).fillna(1)).clip(0, 1)
    rec["estimated_carrying_cost"] = (rec["current_inventory"] * holding_cost / 52).round(2)
    rec["recommended_carrying_cost"] = ((rec["reorder_point_recommended"] + rec["economic_order_quantity"] / 2) * holding_cost / 52).round(2)
    rec["potential_weekly_savings"] = (
        (rec["current_stockout_rate"] - rec["estimated_stockout_risk"]).clip(lower=0) * rec["avg_weekly_demand"] * float(config["inventory"]["stockout_cost"])
        + (rec["estimated_carrying_cost"] - rec["recommended_carrying_cost"]).clip(lower=0)
    ).round(2)
    rec["policy_status"] = np.where(rec["weeks_observed"] < 8, "Insufficient history", "Recommended")
    rec.to_csv(output_dir / "inventory_recommendations.csv", index=False)
    return rec


def optimize_shipment_allocation(tables: dict[str, pd.DataFrame], config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Optimize carrier-mode allocation shares by priority using linear programming."""
    shipments = tables["shipments"].copy()
    perf = shipments.groupby(["priority_level", "carrier", "transport_mode"], as_index=False).agg(
        avg_cost=("shipping_cost", "mean"),
        avg_transit_days=("supplier_lead_time_days", "mean"),
        reliability=("late_delivery_flag", lambda s: 1 - s.mean()),
        observed_shipments=("shipment_id", "count"),
    )
    demand = shipments.groupby("priority_level", as_index=False).agg(required_shipments=("shipment_id", "count"))
    results = []
    for priority, group in perf.groupby("priority_level"):
        required = int(demand.loc[demand["priority_level"].eq(priority), "required_shipments"].iloc[0])
        c = (group["avg_cost"] * (1 + float(config["optimization"]["reliability_weight"]) * (1 - group["reliability"]))).to_numpy()
        capacity = (group["observed_shipments"] * float(config["optimization"]["capacity_buffer"])).to_numpy()
        current_reliability = float(np.average(group["reliability"], weights=group["observed_shipments"]))
        A_ub = np.vstack([np.eye(len(group)), -group["reliability"].to_numpy().reshape(1, -1)])
        b_ub = np.concatenate([capacity, np.array([-current_reliability * required])])
        A_eq = np.ones((1, len(group)))
        b_eq = np.array([required])
        bounds = [(0, None)] * len(group)
        sol = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
        if not sol.success:
            allocation = group["observed_shipments"].to_numpy(dtype=float)
        else:
            allocation = sol.x
        out = group.copy()
        out["optimized_shipments_exact"] = allocation
        out["optimized_shipments"] = allocation.round(0)
        out["current_cost"] = out["avg_cost"] * out["observed_shipments"]
        out["optimized_cost"] = out["avg_cost"] * out["optimized_shipments_exact"]
        out["capacity_utilization"] = out["optimized_shipments_exact"] / capacity
        results.append(out)
    allocation = pd.concat(results, ignore_index=True)
    summary = {
        "current_allocation_cost": float(allocation["current_cost"].sum()),
        "optimized_allocation_cost": float(allocation["optimized_cost"].sum()),
        "estimated_savings": float(allocation["current_cost"].sum() - allocation["optimized_cost"].sum()),
        "expected_on_time_rate_current": float(np.average(allocation["reliability"], weights=allocation["observed_shipments"])),
        "expected_on_time_rate_optimized": float(np.average(allocation["reliability"], weights=allocation["optimized_shipments"].clip(lower=0.0001))),
        "max_capacity_utilization": float(allocation["capacity_utilization"].max()),
        "limitation": "Allocation is optimized by carrier-mode-priority group, not individual route sequencing or vehicle routing.",
    }
    allocation.to_csv(output_dir / "shipment_allocation_optimization.csv", index=False)
    pd.DataFrame([summary]).to_csv(output_dir / "shipment_allocation_optimization_summary.csv", index=False)
    return summary
