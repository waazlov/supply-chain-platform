"""Pipeline and dashboard utility tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.dashboard_utils import load_csv
from src.ingestion import read_tables
from src.pipeline import run_pipeline


def test_missing_file_handling(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_tables(tmp_path)


def test_pipeline_execution_small_config(small_config: dict) -> None:
    summary = run_pipeline("all", small_config)
    assert summary["stage"] == "all"
    assert Path(small_config["paths"]["database"]).exists()
    assert (Path(small_config["paths"]["reports"]) / "pipeline_execution_summary.json").exists()


def test_dashboard_load_csv_missing_file_returns_empty_frame() -> None:
    df = load_csv("missing_file_for_test.csv")
    assert df.empty

