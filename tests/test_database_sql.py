"""DuckDB and SQL transformation tests."""

from __future__ import annotations

from pathlib import Path

from src.cleaning import clean_tables
from src.database import (
    connect_database,
    export_dashboard_tables,
    load_tables_to_duckdb,
    run_sql_scripts,
)


def test_sql_transformations_create_analytics_tables(small_tables: dict, small_config: dict) -> None:
    tables = clean_tables(small_tables, small_config)
    Path(small_config["paths"]["output_data"]).mkdir(parents=True, exist_ok=True)
    load_tables_to_duckdb(tables, small_config)
    run_sql_scripts(small_config)
    export_dashboard_tables(small_config)
    with connect_database(small_config) as con:
        count = con.execute("SELECT COUNT(*) FROM executive_kpi_summary").fetchone()[0]
    assert count == 1
    assert (Path(small_config["paths"]["output_data"]) / "supplier_scorecard.csv").exists()

