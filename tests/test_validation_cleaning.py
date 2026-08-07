"""Validation and cleaning tests."""

from __future__ import annotations

from src.cleaning import clean_tables
from src.validation import validate_tables


def test_validation_finds_intentional_quality_issues(small_tables: dict, small_config: dict) -> None:
    result = validate_tables(small_tables, small_config)
    assert result.summary.iloc[0]["total_records_processed"] > 0
    assert result.issues["invalid_count"].sum() > 0
    assert (result.issues["rule"] == "transport_mode invalid category").any()


def test_cleaning_removes_invalid_values(small_tables: dict, small_config: dict) -> None:
    cleaned = clean_tables(small_tables, small_config)
    shipments = cleaned["shipments"]
    assert shipments["shipment_id"].is_unique
    assert (shipments["quantity"] > 0).all()
    assert (shipments["shipping_cost"] >= 0).all()
    assert shipments["carrier"].isna().sum() == 0
    assert set(shipments["transport_mode"].unique()) <= {"Truck", "Rail", "Air", "Ocean"}

