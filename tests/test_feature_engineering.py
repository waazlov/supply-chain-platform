"""Feature engineering tests."""

from __future__ import annotations

from src.cleaning import clean_tables
from src.feature_engineering import add_shipment_features, build_model_frame


def test_feature_engineering_outputs_expected_columns(small_tables: dict, small_config: dict) -> None:
    tables = clean_tables(small_tables, small_config)
    features = add_shipment_features(tables["shipments"])
    assert {"delay_days", "cost_per_km", "inventory_gap", "delay_cost_estimate"} <= set(features.columns)
    assert (features["delay_days"] >= 0).all()


def test_model_frame_contains_no_delivery_leakage_features(small_tables: dict, small_config: dict) -> None:
    tables = clean_tables(small_tables, small_config)
    frame = build_model_frame(tables["shipments"], tables["products"], tables["suppliers"], tables["routes"])
    assert "actual_delivery_date" in frame.columns
    assert "reliability_score" in frame.columns

