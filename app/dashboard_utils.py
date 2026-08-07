"""Shared Streamlit dashboard helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "output"
REPORT_DIR = ROOT / "reports"


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    """Load a dashboard output table."""
    path = OUTPUT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def require_data(*frames: pd.DataFrame) -> bool:
    """Display a setup hint when required data is missing."""
    if any(frame.empty for frame in frames):
        st.info("Pipeline outputs are not available yet. Run `python scripts/run_pipeline.py all`.")
        return False
    return True


def kpi(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply common filters when matching columns are present."""
    filtered = df.copy()
    st.sidebar.header("Filters")
    if "order_month" in filtered.columns:
        months = sorted(filtered["order_month"].dropna().unique().tolist())
        selected = st.sidebar.multiselect("Month", months, default=months[-6:] if len(months) > 6 else months)
        if selected:
            filtered = filtered[filtered["order_month"].isin(selected)]
    for column, label in [
        ("product_category", "Product category"),
        ("supplier_id", "Supplier"),
        ("warehouse_id", "Warehouse"),
        ("carrier", "Carrier"),
        ("transport_mode", "Mode"),
        ("route_id", "Route"),
        ("customer_region", "Customer region"),
        ("priority_level", "Priority"),
    ]:
        if column in filtered.columns:
            values = sorted(filtered[column].dropna().astype(str).unique().tolist())
            selected = st.sidebar.multiselect(label, values)
            if selected:
                filtered = filtered[filtered[column].astype(str).isin(selected)]
    return filtered

