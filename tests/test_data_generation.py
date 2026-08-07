"""Data generation tests."""

from __future__ import annotations

from src.data_generation import generate_synthetic_data


def test_data_generation_is_reproducible(small_config: dict) -> None:
    first = generate_synthetic_data(small_config)
    second = generate_synthetic_data(small_config)
    assert first["shipments"].head(20).equals(second["shipments"].head(20))
    assert len(first["shipments"]) >= small_config["data_generation"]["shipments"]
    assert {"shipments", "orders", "products", "suppliers", "warehouses", "customers", "routes", "inventory_snapshots", "purchase_orders", "calendar"} <= set(first)

