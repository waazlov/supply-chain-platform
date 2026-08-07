"""DuckDB database loading and SQL transformation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from src.feature_engineering import add_shipment_features
from src.utils import configured_path


def connect_database(config: dict[str, Any]) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection at the configured path."""
    db_path = configured_path(config, "database")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def load_tables_to_duckdb(tables: dict[str, pd.DataFrame], config: dict[str, Any]) -> None:
    """Replace base and feature tables in DuckDB."""
    with connect_database(config) as con:
        for name, table in tables.items():
            con.register(f"{name}_df", table)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM {name}_df")
            con.unregister(f"{name}_df")
        shipment_features = add_shipment_features(tables["shipments"])
        con.register("shipment_features_df", shipment_features)
        con.execute("CREATE OR REPLACE TABLE shipment_features AS SELECT * FROM shipment_features_df")
        con.unregister("shipment_features_df")


def run_sql_scripts(config: dict[str, Any], sql_dir: Path | None = None) -> None:
    """Run SQL transformation scripts in sorted order."""
    directory = sql_dir or Path("sql")
    with connect_database(config) as con:
        for script in sorted(directory.glob("*.sql")):
            con.execute(script.read_text(encoding="utf-8"))


def export_dashboard_tables(config: dict[str, Any]) -> None:
    """Export analytics tables to dashboard-ready CSV files."""
    output_dir = configured_path(config, "output_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = [
        "shipment_performance_summary",
        "supplier_scorecard",
        "carrier_performance_scorecard",
        "route_performance_summary",
        "warehouse_utilization_summary",
        "product_demand_summary",
        "inventory_risk_summary",
        "monthly_logistics_cost_summary",
        "late_delivery_root_cause_summary",
        "executive_kpi_summary",
    ]
    with connect_database(config) as con:
        for table in tables:
            con.execute(f"COPY (SELECT * FROM {table}) TO '{str(output_dir / f'{table}.csv').replace(chr(92), '/')}' (HEADER, DELIMITER ',')")


def table_counts(config: dict[str, Any]) -> dict[str, int]:
    """Return row counts for all user tables in the database."""
    with connect_database(config) as con:
        names = con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
        ).fetchdf()["table_name"].tolist()
        return {name: int(con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]) for name in names}

