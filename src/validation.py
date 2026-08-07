"""Data quality validation for relational supply chain tables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils import write_html_table

APPROVED = {
    "transport_mode": {"Truck", "Rail", "Air", "Ocean"},
    "priority_level": {"Standard", "Expedited", "Critical"},
    "shipment_status": {"Delivered Late", "Delivered On Time", "Backordered"},
}


@dataclass
class QualityResult:
    """Validation output with issue-level detail and summary metrics."""

    issues: pd.DataFrame
    summary: pd.DataFrame


def _issue(table: str, rule: str, count: int, severity: str = "error") -> dict[str, Any]:
    return {"table": table, "rule": rule, "invalid_count": int(count), "severity": severity}


def validate_tables(tables: dict[str, pd.DataFrame], config: dict[str, Any]) -> QualityResult:
    """Validate primary keys, foreign keys, business rules, and outlier indicators."""
    issues: list[dict[str, Any]] = []
    pk_map = {
        "shipments": "shipment_id",
        "orders": "order_id",
        "products": "product_id",
        "suppliers": "supplier_id",
        "warehouses": "warehouse_id",
        "customers": "customer_id",
        "routes": "route_id",
        "purchase_orders": "purchase_order_id",
    }
    required = {
        "shipments": [
            "shipment_id", "order_id", "product_id", "supplier_id", "warehouse_id", "customer_id",
            "route_id", "carrier", "transport_mode", "order_date", "ship_date", "expected_delivery_date",
            "actual_delivery_date", "shipping_cost", "quantity", "late_delivery_flag",
        ],
        "orders": ["order_id", "customer_id", "product_id", "order_date", "quantity", "unit_price"],
    }
    for table_name, pk in pk_map.items():
        if table_name in tables:
            issues.append(_issue(table_name, f"primary key {pk} duplicates", tables[table_name][pk].duplicated().sum()))
    for table_name, columns in required.items():
        table = tables[table_name]
        for column in columns:
            issues.append(_issue(table_name, f"required field {column} nulls", table[column].isna().sum()))

    shipments = tables["shipments"]
    orders = tables["orders"]
    issues.extend([
        _issue("shipments", "order_id foreign key mismatch", (~shipments["order_id"].isin(orders["order_id"])).sum()),
        _issue("shipments", "product_id foreign key mismatch", (~shipments["product_id"].isin(tables["products"]["product_id"])).sum()),
        _issue("shipments", "supplier_id foreign key mismatch", (~shipments["supplier_id"].isin(tables["suppliers"]["supplier_id"])).sum()),
        _issue("shipments", "warehouse_id foreign key mismatch", (~shipments["warehouse_id"].isin(tables["warehouses"]["warehouse_id"])).sum()),
        _issue("shipments", "customer_id foreign key mismatch", (~shipments["customer_id"].isin(tables["customers"]["customer_id"])).sum()),
        _issue("shipments", "route_id foreign key mismatch", (~shipments["route_id"].isin(tables["routes"]["route_id"])).sum()),
        _issue("shipments", "quantity must be positive", (shipments["quantity"] <= 0).sum()),
        _issue("shipments", "shipping_cost cannot be negative", (shipments["shipping_cost"] < 0).sum()),
        _issue("shipments", "fuel_cost cannot be negative", (shipments["fuel_cost"] < 0).sum()),
        _issue("shipments", "inventory_level cannot be negative", (shipments["inventory_level"] < 0).sum()),
        _issue("shipments", "reorder_point cannot be negative", (shipments["reorder_point"] < 0).sum()),
        _issue("shipments", "weather_severity outside 0 to 1", (~shipments["weather_severity"].between(0, 1)).sum()),
        _issue("shipments", "route_congestion_score outside 0 to 1", (~shipments["route_congestion_score"].between(0, 1)).sum()),
    ])
    for column, allowed in APPROVED.items():
        issues.append(_issue("shipments", f"{column} invalid category", (~shipments[column].isin(allowed) & shipments[column].notna()).sum()))

    ship_date = pd.to_datetime(shipments["ship_date"], errors="coerce")
    order_date = pd.to_datetime(shipments["order_date"], errors="coerce")
    actual = pd.to_datetime(shipments["actual_delivery_date"], errors="coerce")
    issues.extend([
        _issue("shipments", "ship_date before order_date", (ship_date < order_date).sum()),
        _issue("shipments", "actual_delivery_date before ship_date", (actual < ship_date).sum()),
    ])
    outlier_cutoff = shipments["shipping_cost"].quantile(config["validation"]["shipping_cost_outlier_quantile"])
    issues.append(_issue("shipments", "shipping_cost extreme value", (shipments["shipping_cost"] > outlier_cutoff).sum(), "warning"))

    issue_df = pd.DataFrame(issues)
    missing_long = []
    for table_name, table in tables.items():
        for column, count in table.isna().sum().items():
            if count:
                missing_long.append(_issue(table_name, f"missing values in {column}", count, "warning"))
    if missing_long:
        issue_df = pd.concat([issue_df, pd.DataFrame(missing_long)], ignore_index=True)

    total_records = sum(len(table) for table in tables.values())
    summary = pd.DataFrame([{
        "total_records_processed": total_records,
        "duplicate_counts": int(shipments["shipment_id"].duplicated().sum()),
        "invalid_records_by_rule": int(issue_df.loc[issue_df["severity"].eq("error"), "invalid_count"].sum()),
        "outlier_counts": int(issue_df.loc[issue_df["rule"].str.contains("extreme"), "invalid_count"].sum()),
        "records_rejected": int(((shipments["quantity"] <= 0) | (shipments["shipping_cost"] < 0)).sum()),
        "records_corrected": int(shipments["carrier"].isna().sum() + (~shipments["transport_mode"].isin(APPROVED["transport_mode"]) & shipments["transport_mode"].notna()).sum()),
        "final_valid_record_count": len(shipments.drop_duplicates("shipment_id")),
    }])
    return QualityResult(issue_df, summary)


def save_quality_report(result: QualityResult, output_dir: Path) -> None:
    """Save quality reports as CSV and HTML."""
    output_dir.mkdir(parents=True, exist_ok=True)
    result.issues.to_csv(output_dir / "data_quality_issues.csv", index=False)
    result.summary.to_csv(output_dir / "data_quality_summary.csv", index=False)
    write_html_table(result.issues, output_dir / "data_quality_report.html", "Data Quality Report")

