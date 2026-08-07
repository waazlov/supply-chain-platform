"""CSV ingestion utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

TABLES = [
    "shipments", "orders", "products", "suppliers", "warehouses", "customers",
    "routes", "inventory_snapshots", "purchase_orders", "calendar",
]


def read_tables(data_dir: Path) -> dict[str, pd.DataFrame]:
    """Read required CSV tables from a directory."""
    tables = {}
    missing = []
    for table in TABLES:
        path = data_dir / f"{table}.csv"
        if not path.exists():
            missing.append(str(path))
        else:
            tables[table] = pd.read_csv(path)
    if missing:
        raise FileNotFoundError("Missing required table files: " + ", ".join(missing))
    return tables


def write_tables(tables: dict[str, pd.DataFrame], data_dir: Path) -> None:
    """Write table dictionary to CSV files."""
    data_dir.mkdir(parents=True, exist_ok=True)
    for table_name, table in tables.items():
        table.to_csv(data_dir / f"{table_name}.csv", index=False)

