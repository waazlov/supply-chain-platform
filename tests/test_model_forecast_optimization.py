"""Model, forecast, and optimization tests."""

from __future__ import annotations

from pathlib import Path

from src.cleaning import clean_tables
from src.forecasting import train_demand_forecasts
from src.modeling import train_late_delivery_model
from src.optimization import optimize_inventory, optimize_shipment_allocation


def test_model_training_and_prediction_outputs(small_tables: dict, small_config: dict) -> None:
    tables = clean_tables(small_tables, small_config)
    metrics = train_late_delivery_model(tables, small_config, Path(small_config["paths"]["models"]), Path(small_config["paths"]["output_data"]))
    assert "test" in metrics
    assert 0 <= metrics["test"]["recall"] <= 1
    assert (Path(small_config["paths"]["models"]) / "late_delivery_model.joblib").exists()
    assert (Path(small_config["paths"]["output_data"]) / "late_delivery_scored_shipments.csv").exists()


def test_forecast_output_format(small_tables: dict, small_config: dict) -> None:
    tables = clean_tables(small_tables, small_config)
    metrics = train_demand_forecasts(tables, small_config, Path(small_config["paths"]["output_data"]), Path(small_config["paths"]["models"]))
    assert "hist_gradient_boosting" in metrics
    assert (Path(small_config["paths"]["output_data"]) / "demand_forecast.csv").exists()


def test_inventory_and_allocation_optimization(small_tables: dict, small_config: dict) -> None:
    tables = clean_tables(small_tables, small_config)
    inventory = optimize_inventory(tables, small_config, Path(small_config["paths"]["output_data"]))
    allocation = optimize_shipment_allocation(tables, small_config, Path(small_config["paths"]["output_data"]))
    assert {"safety_stock", "economic_order_quantity", "recommended_order_quantity"} <= set(inventory.columns)
    assert allocation["optimized_allocation_cost"] > 0
    assert allocation["max_capacity_utilization"] <= 1.01

