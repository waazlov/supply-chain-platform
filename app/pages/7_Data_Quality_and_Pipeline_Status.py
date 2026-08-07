"""Data quality and pipeline status page."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard_utils import REPORT_DIR, load_csv, require_data

st.title("Data Quality and Pipeline Status")
issues = load_csv("data_quality_issues.csv")
summary = load_csv("data_quality_summary.csv")
if require_data(issues, summary):
    st.dataframe(summary, width="stretch")
    nonzero = issues[issues["invalid_count"] > 0].sort_values("invalid_count", ascending=False)
    st.plotly_chart(px.bar(nonzero.head(25), x="invalid_count", y="rule", color="severity", orientation="h", title="Largest Data Quality Findings"), width="stretch")
    pipeline_summary = REPORT_DIR / "pipeline_execution_summary.json"
    if pipeline_summary.exists():
        st.json(json.loads(pipeline_summary.read_text(encoding="utf-8")))
    st.subheader("Insight")
    st.write("The validation layer separates rejected records, corrected records, warning-level outliers, and final valid records so dashboard users can judge whether outputs are fit for use.")
