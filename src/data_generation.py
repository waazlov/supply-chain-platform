"""Synthetic logistics data generation with deterministic operational patterns."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GeneratedTables:
    """Container for generated relational tables."""

    shipments: pd.DataFrame
    orders: pd.DataFrame
    products: pd.DataFrame
    suppliers: pd.DataFrame
    warehouses: pd.DataFrame
    customers: pd.DataFrame
    routes: pd.DataFrame
    inventory_snapshots: pd.DataFrame
    purchase_orders: pd.DataFrame
    calendar: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return self.__dict__.copy()


def _choice(rng: np.random.Generator, values: list[str], size: int, p: list[float] | None = None) -> np.ndarray:
    return rng.choice(np.array(values), size=size, p=p)


def generate_synthetic_data(config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Generate two years of related supply chain data with embedded business patterns."""
    seed = int(config["random_seed"])
    rng = np.random.default_rng(seed)
    start = pd.Timestamp(config["date_range"]["start"])
    end = pd.Timestamp(config["date_range"]["end"])
    dates = pd.date_range(start, end, freq="D")
    n_shipments = int(config["data_generation"]["shipments"])

    categories = ["Electronics", "Apparel", "Home", "Industrial", "Grocery", "Healthcare"]
    products = pd.DataFrame({
        "product_id": [f"P{i:04d}" for i in range(1, config["data_generation"]["products"] + 1)],
        "product_category": _choice(rng, categories, config["data_generation"]["products"], [0.18, 0.18, 0.16, 0.16, 0.20, 0.12]),
        "unit_price": rng.lognormal(mean=3.5, sigma=0.55, size=config["data_generation"]["products"]).round(2),
        "unit_cost": rng.lognormal(mean=3.0, sigma=0.5, size=config["data_generation"]["products"]).round(2),
        "shelf_life_days": rng.choice([30, 60, 90, 180, 365, 730], size=config["data_generation"]["products"]),
        "intermittent_demand_flag": rng.choice([0, 1], size=config["data_generation"]["products"], p=[0.82, 0.18]),
    })
    products["unit_cost"] = np.minimum(products["unit_cost"], products["unit_price"] * 0.82).round(2)

    suppliers = pd.DataFrame({
        "supplier_id": [f"S{i:03d}" for i in range(1, config["data_generation"]["suppliers"] + 1)],
        "supplier_name": [f"Supplier {i:02d}" for i in range(1, config["data_generation"]["suppliers"] + 1)],
        "supplier_region": _choice(rng, ["West", "Midwest", "South", "Northeast", "International"], config["data_generation"]["suppliers"]),
        "base_lead_time_days": rng.integers(3, 24, size=config["data_generation"]["suppliers"]),
        "defect_rate": rng.uniform(0.006, 0.055, size=config["data_generation"]["suppliers"]).round(4),
        "reliability_score": rng.uniform(0.78, 0.98, size=config["data_generation"]["suppliers"]).round(3),
    })
    suppliers.loc[suppliers.index.isin([2, 11, 17]), ["defect_rate", "base_lead_time_days"]] = [0.095, 28]

    warehouses = pd.DataFrame({
        "warehouse_id": [f"W{i:02d}" for i in range(1, config["data_generation"]["warehouses"] + 1)],
        "warehouse_region": _choice(rng, ["West", "Midwest", "South", "Northeast"], config["data_generation"]["warehouses"]),
        "capacity_units": rng.integers(22000, 70000, size=config["data_generation"]["warehouses"]),
        "labor_shift_count": rng.choice([2, 3], size=config["data_generation"]["warehouses"], p=[0.35, 0.65]),
    })

    customers = pd.DataFrame({
        "customer_id": [f"C{i:05d}" for i in range(1, config["data_generation"]["customers"] + 1)],
        "customer_region": _choice(rng, ["West", "Midwest", "South", "Northeast"], config["data_generation"]["customers"]),
        "customer_segment": _choice(rng, ["Retail", "Wholesale", "Ecommerce", "Distributor"], config["data_generation"]["customers"], [0.34, 0.2, 0.32, 0.14]),
    })

    modes = ["Truck", "Rail", "Air", "Ocean"]
    carriers = ["Apex Freight", "BlueLine", "NorthStar", "ParcelPro", "TransGlobal", "Velocity"]
    routes = pd.DataFrame({
        "route_id": [f"R{i:03d}" for i in range(1, config["data_generation"]["routes"] + 1)],
        "origin_region": _choice(rng, ["West", "Midwest", "South", "Northeast"], config["data_generation"]["routes"]),
        "destination_region": _choice(rng, ["West", "Midwest", "South", "Northeast"], config["data_generation"]["routes"]),
        "default_mode": _choice(rng, modes, config["data_generation"]["routes"], [0.58, 0.18, 0.16, 0.08]),
        "distance_km": rng.integers(120, 4200, size=config["data_generation"]["routes"]),
        "route_capacity_per_week": rng.integers(3500, 15000, size=config["data_generation"]["routes"]),
        "base_congestion_score": rng.uniform(0.12, 0.82, size=config["data_generation"]["routes"]).round(3),
    })

    order_dates = rng.choice(dates, size=n_shipments)
    order_dates = pd.to_datetime(order_dates)
    product_idx = rng.integers(0, len(products), size=n_shipments)
    supplier_idx = rng.integers(0, len(suppliers), size=n_shipments)
    warehouse_idx = rng.integers(0, len(warehouses), size=n_shipments)
    customer_idx = rng.integers(0, len(customers), size=n_shipments)
    route_idx = rng.integers(0, len(routes), size=n_shipments)
    priority = _choice(rng, ["Standard", "Expedited", "Critical"], n_shipments, [0.72, 0.22, 0.06])
    mode = routes.loc[route_idx, "default_mode"].to_numpy()
    air_upgrade = (priority != "Standard") & (rng.random(n_shipments) < 0.22)
    mode[air_upgrade] = "Air"
    carrier = _choice(rng, carriers, n_shipments, [0.21, 0.17, 0.16, 0.22, 0.13, 0.11])
    season = pd.Series(order_dates).dt.month.isin([11, 12, 1]).to_numpy()
    weather = np.clip(rng.beta(2.2, 5.5, n_shipments) + season * rng.uniform(0.08, 0.28, n_shipments), 0, 1)
    congestion = np.clip(routes.loc[route_idx, "base_congestion_score"].to_numpy() + season * 0.11 + rng.normal(0, 0.08, n_shipments), 0, 1)
    supplier_lead = suppliers.loc[supplier_idx, "base_lead_time_days"].to_numpy() + rng.poisson(2.0, n_shipments)
    processing = np.clip(rng.normal(18, 7, n_shipments) + congestion * 18 + (warehouses.loc[warehouse_idx, "labor_shift_count"].to_numpy() == 2) * 8, 2, 96)
    distance = routes.loc[route_idx, "distance_km"].to_numpy() * rng.normal(1.0, 0.035, n_shipments)
    quantity_base = rng.lognormal(mean=2.25, sigma=0.75, size=n_shipments)
    intermittent = products.loc[product_idx, "intermittent_demand_flag"].to_numpy() == 1
    quantity = np.where(intermittent & (rng.random(n_shipments) < 0.45), 1, quantity_base).round().astype(int)
    quantity = np.clip(quantity, 1, 280)
    unit_price = products.loc[product_idx, "unit_price"].to_numpy()
    fuel_cost = (distance * rng.uniform(0.08, 0.22, n_shipments)).round(2)
    mode_multiplier = pd.Series(mode).map({"Truck": 1.0, "Rail": 0.72, "Air": 2.35, "Ocean": 0.58}).to_numpy()
    priority_multiplier = pd.Series(priority).map({"Standard": 1.0, "Expedited": 1.28, "Critical": 1.72}).to_numpy()
    carrier_noise = pd.Series(carrier).map({"Apex Freight": 1.0, "BlueLine": 0.93, "NorthStar": 1.08, "ParcelPro": 1.14, "TransGlobal": 0.9, "Velocity": 1.22}).to_numpy()
    shipping_cost = ((distance * 0.42 + quantity * 1.7 + fuel_cost) * mode_multiplier * priority_multiplier * carrier_noise).round(2)
    base_transit = distance / pd.Series(mode).map({"Truck": 520, "Rail": 410, "Air": 1500, "Ocean": 240}).to_numpy()
    transit_days = base_transit + weather * 2.9 + congestion * 2.2 + rng.normal(0.4, 1.05, n_shipments)
    expected_days = np.ceil(base_transit + pd.Series(priority).map({"Standard": 2.0, "Expedited": 1.2, "Critical": 0.7}).to_numpy()).astype(int)
    carrier_delay = pd.Series(carrier).map({"Apex Freight": 0.1, "BlueLine": -0.2, "NorthStar": 0.35, "ParcelPro": 0.65, "TransGlobal": -0.25, "Velocity": 0.2}).to_numpy()
    transit_days = np.maximum(1, np.ceil(transit_days + carrier_delay)).astype(int)
    ship_delay = np.ceil(processing / 24).astype(int)
    ship_dates = order_dates + pd.to_timedelta(ship_delay, unit="D")
    expected_delivery = ship_dates + pd.to_timedelta(expected_days, unit="D")
    actual_delivery = ship_dates + pd.to_timedelta(transit_days, unit="D")
    inventory_level = np.maximum(0, rng.normal(650, 260, n_shipments) - quantity * rng.uniform(0.4, 1.4, n_shipments)).round().astype(int)
    reorder_point = rng.integers(120, 520, size=n_shipments)
    stockout = (inventory_level < quantity) | ((inventory_level < reorder_point) & (supplier_lead > 18) & (rng.random(n_shipments) < 0.34))
    defect = rng.random(n_shipments) < suppliers.loc[supplier_idx, "defect_rate"].to_numpy()
    late = actual_delivery > expected_delivery
    status = np.where(late, "Delivered Late", "Delivered On Time")
    status = np.where(stockout & (rng.random(n_shipments) < 0.2), "Backordered", status)

    orders = pd.DataFrame({
        "order_id": [f"O{i:08d}" for i in range(1, n_shipments + 1)],
        "customer_id": customers.loc[customer_idx, "customer_id"].to_numpy(),
        "product_id": products.loc[product_idx, "product_id"].to_numpy(),
        "order_date": order_dates.strftime("%Y-%m-%d"),
        "quantity": quantity,
        "unit_price": unit_price.round(2),
        "order_value": (quantity * unit_price).round(2),
        "priority_level": priority,
    })

    shipments = pd.DataFrame({
        "shipment_id": [f"SH{i:08d}" for i in range(1, n_shipments + 1)],
        "order_id": orders["order_id"],
        "product_id": orders["product_id"],
        "supplier_id": suppliers.loc[supplier_idx, "supplier_id"].to_numpy(),
        "warehouse_id": warehouses.loc[warehouse_idx, "warehouse_id"].to_numpy(),
        "customer_id": orders["customer_id"],
        "route_id": routes.loc[route_idx, "route_id"].to_numpy(),
        "carrier": carrier,
        "transport_mode": mode,
        "order_date": orders["order_date"],
        "ship_date": ship_dates.strftime("%Y-%m-%d"),
        "expected_delivery_date": expected_delivery.strftime("%Y-%m-%d"),
        "actual_delivery_date": actual_delivery.strftime("%Y-%m-%d"),
        "distance_km": distance.round(1),
        "shipping_cost": shipping_cost,
        "fuel_cost": fuel_cost,
        "quantity": quantity,
        "unit_price": unit_price.round(2),
        "inventory_level": inventory_level,
        "reorder_point": reorder_point,
        "supplier_lead_time_days": supplier_lead,
        "warehouse_processing_hours": processing.round(1),
        "weather_severity": weather.round(3),
        "route_congestion_score": congestion.round(3),
        "shipment_status": status,
        "priority_level": priority,
        "defect_flag": defect.astype(int),
        "stockout_flag": stockout.astype(int),
        "late_delivery_flag": late.astype(int),
    })

    # Deterministic dirty records used by validation and cleaning tests.
    dirty = shipments.sample(60, random_state=seed).copy()
    shipments = pd.concat([shipments, dirty], ignore_index=True)
    shipments.loc[5:12, "carrier"] = np.nan
    shipments.loc[20:24, "transport_mode"] = "Drone"
    shipments.loc[30:33, "quantity"] = -3
    shipments.loc[40:43, "shipping_cost"] = -50
    shipments.loc[50:52, "actual_delivery_date"] = shipments.loc[50:52, "ship_date"]
    shipments.loc[60:61, "shipping_cost"] = shipments["shipping_cost"].quantile(0.99) * 9

    calendar = pd.DataFrame({"date": dates.strftime("%Y-%m-%d")})
    calendar["year"] = pd.to_datetime(calendar["date"]).dt.year
    calendar["month"] = pd.to_datetime(calendar["date"]).dt.month
    calendar["week"] = pd.to_datetime(calendar["date"]).dt.isocalendar().week.astype(int)
    calendar["quarter"] = pd.to_datetime(calendar["date"]).dt.quarter
    calendar["is_peak_season"] = calendar["month"].isin([11, 12, 1]).astype(int)

    week_dates = pd.date_range(start, end, freq="W-MON")
    inv_rows = []
    for product_id in products["product_id"]:
        for warehouse_id in warehouses["warehouse_id"]:
            base = rng.integers(180, 1300)
            trend = rng.normal(0, 1.4, len(week_dates)).cumsum()
            levels = np.maximum(0, base + trend + rng.normal(0, 90, len(week_dates))).round().astype(int)
            inv_rows.append(pd.DataFrame({
                "snapshot_date": week_dates.strftime("%Y-%m-%d"),
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "inventory_level": levels,
                "reorder_point": rng.integers(90, 460, len(week_dates)),
            }))
    inventory_snapshots = pd.concat(inv_rows, ignore_index=True)

    po_count = max(2500, n_shipments // 12)
    po_dates = pd.to_datetime(rng.choice(dates, size=po_count))
    purchase_orders = pd.DataFrame({
        "purchase_order_id": [f"PO{i:07d}" for i in range(1, po_count + 1)],
        "supplier_id": rng.choice(suppliers["supplier_id"], size=po_count),
        "product_id": rng.choice(products["product_id"], size=po_count),
        "warehouse_id": rng.choice(warehouses["warehouse_id"], size=po_count),
        "order_date": po_dates.strftime("%Y-%m-%d"),
        "ordered_quantity": rng.integers(80, 2200, size=po_count),
        "expected_lead_time_days": rng.integers(4, 30, size=po_count),
    })
    purchase_orders["received_date"] = (
        po_dates + pd.to_timedelta(purchase_orders["expected_lead_time_days"] + rng.integers(-2, 7, size=po_count), unit="D")
    ).dt.strftime("%Y-%m-%d")

    return GeneratedTables(
        shipments=shipments,
        orders=orders,
        products=products,
        suppliers=suppliers,
        warehouses=warehouses,
        customers=customers,
        routes=routes,
        inventory_snapshots=inventory_snapshots,
        purchase_orders=purchase_orders,
        calendar=calendar,
    ).as_dict()


def write_raw_tables(tables: dict[str, pd.DataFrame], raw_dir: Path) -> None:
    """Write generated tables as CSV files."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(raw_dir / f"{name}.csv", index=False)

