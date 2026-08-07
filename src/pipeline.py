"""End-to-end supply chain analytics pipeline orchestration."""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd

from src.analytics import build_eda_report
from src.cleaning import clean_tables
from src.data_generation import generate_synthetic_data, write_raw_tables
from src.database import export_dashboard_tables, load_tables_to_duckdb, run_sql_scripts, table_counts
from src.forecasting import train_demand_forecasts
from src.ingestion import read_tables, write_tables
from src.modeling import train_late_delivery_model
from src.optimization import optimize_inventory, optimize_shipment_allocation
from src.reporting import generate_executive_report
from src.utils import configured_path, ensure_directories, setup_logging, write_json
from src.validation import save_quality_report, validate_tables


LOGGER = logging.getLogger(__name__)


def _copy_quality_outputs(config: dict[str, Any]) -> None:
    reports = configured_path(config, "reports")
    output = configured_path(config, "output_data")
    for name in ["data_quality_issues.csv", "data_quality_summary.csv"]:
        src = reports / name
        if src.exists():
            pd.read_csv(src).to_csv(output / name, index=False)


def run_pipeline(stage: str, config: dict[str, Any]) -> dict[str, Any]:
    """Run a named pipeline stage or the full pipeline."""
    ensure_directories(config)
    log_file = setup_logging(config, stage)
    start = time.perf_counter()
    raw_dir = configured_path(config, "raw_data")
    processed_dir = configured_path(config, "processed_data")
    output_dir = configured_path(config, "output_data")
    model_dir = configured_path(config, "models")
    report_dir = configured_path(config, "reports")
    summary: dict[str, Any] = {"stage": stage, "log_file": str(log_file), "stages": []}

    def mark(name: str, fn):
        stage_start = time.perf_counter()
        LOGGER.info("Starting stage: %s", name)
        result = fn()
        elapsed = time.perf_counter() - stage_start
        LOGGER.info("Finished stage: %s in %.2fs", name, elapsed)
        summary["stages"].append({"stage": name, "seconds": round(elapsed, 2)})
        return result

    if stage in {"generate", "all"}:
        tables = mark("generate", lambda: generate_synthetic_data(config))
        mark("write_raw", lambda: write_raw_tables(tables, raw_dir))
    if stage in {"ingest", "validate", "transform", "train", "optimize", "report", "all"}:
        tables = mark("ingest", lambda: read_tables(raw_dir if raw_dir.exists() and list(raw_dir.glob("*.csv")) else processed_dir))
    if stage in {"validate", "all"}:
        quality = mark("validate", lambda: validate_tables(tables, config))
        mark("save_quality", lambda: save_quality_report(quality, report_dir))
        _copy_quality_outputs(config)
    if stage in {"transform", "all"}:
        if "quality" not in locals():
            quality = validate_tables(tables, config)
            save_quality_report(quality, report_dir)
            _copy_quality_outputs(config)
        cleaned = mark("clean", lambda: clean_tables(tables, config))
        mark("write_processed", lambda: write_tables(cleaned, processed_dir))
        mark("load_database", lambda: load_tables_to_duckdb(cleaned, config))
        mark("sql_transform", lambda: run_sql_scripts(config))
        mark("export_dashboard_tables", lambda: export_dashboard_tables(config))
        tables = cleaned
    if stage in {"train", "optimize", "report"}:
        tables = mark("ingest_processed", lambda: read_tables(processed_dir))
    if stage in {"train", "all"}:
        mark("eda_report", lambda: build_eda_report(tables, report_dir))
        model_metrics = mark("late_delivery_model", lambda: train_late_delivery_model(tables, config, model_dir, output_dir))
        forecast_metrics = mark("demand_forecast", lambda: train_demand_forecasts(tables, config, output_dir, model_dir))
        summary["model_metrics"] = model_metrics
        summary["forecast_metrics"] = forecast_metrics
    if stage in {"optimize", "all"}:
        inventory = mark("inventory_optimization", lambda: optimize_inventory(tables, config, output_dir))
        allocation = mark("shipment_allocation_optimization", lambda: optimize_shipment_allocation(tables, config, output_dir))
        summary["inventory_recommendations"] = int(len(inventory))
        summary["allocation"] = allocation
    if stage in {"report", "all"}:
        reports = mark("executive_report", lambda: generate_executive_report(config))
        summary["reports"] = {key: str(value) for key, value in reports.items()}
    if configured_path(config, "database").exists():
        summary["database_table_counts"] = table_counts(config)
    summary["total_seconds"] = round(time.perf_counter() - start, 2)
    write_json(summary, report_dir / "pipeline_execution_summary.json")
    LOGGER.info("Pipeline completed in %.2fs", summary["total_seconds"])
    return summary
