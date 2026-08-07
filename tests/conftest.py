"""Pytest fixtures for small deterministic pipeline tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.data_generation import generate_synthetic_data


@pytest.fixture()
def small_config(tmp_path: Path) -> dict:
    return {
        "project": {"name": "test"},
        "random_seed": 7,
        "paths": {
            "raw_data": str(tmp_path / "raw"),
            "processed_data": str(tmp_path / "processed"),
            "output_data": str(tmp_path / "output"),
            "database": str(tmp_path / "db" / "test.duckdb"),
            "models": str(tmp_path / "models"),
            "reports": str(tmp_path / "reports"),
            "logs": str(tmp_path / "logs"),
        },
        "date_range": {"start": "2024-01-01", "end": "2024-06-30"},
        "data_generation": {
            "shipments": 1200,
            "products": 18,
            "suppliers": 8,
            "warehouses": 4,
            "customers": 50,
            "routes": 10,
        },
        "validation": {"shipping_cost_outlier_quantile": 0.995},
        "modeling": {"test_months": 1, "validation_months": 1, "random_forest_estimators": 20, "late_recall_weight": 0.65},
        "forecasting": {"horizon_weeks": 12, "evaluation_weeks": 6},
        "inventory": {"service_level": 0.95, "holding_cost_rate": 0.22, "ordering_cost": 95.0, "stockout_cost": 45.0, "review_period_days": 7},
        "optimization": {"max_delivery_days_standard": 7, "capacity_buffer": 1.15, "reliability_weight": 0.18},
        "dashboard": {"default_days": 180},
    }


@pytest.fixture()
def small_tables(small_config: dict) -> dict:
    return generate_synthetic_data(small_config)

