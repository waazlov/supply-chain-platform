# Architecture

The project uses a batch analytics architecture:

1. Synthetic data generation or CSV ingestion writes relational raw tables.
2. Validation checks primary keys, required fields, foreign keys, dates, categories, ranges, duplicates, and outliers.
3. Cleaning removes rejected records and corrects recoverable issues.
4. Feature engineering adds business metrics and modeling features.
5. DuckDB stores cleaned relational tables and analytical feature tables.
6. SQL scripts create reusable dashboard-ready analytical summaries.
7. Python modules train the late-delivery classifier, demand forecasts, inventory recommendations, and allocation optimization.
8. Reports and dashboard CSV outputs are exported.
9. Streamlit reads output tables for interactive analysis.

The design keeps SQL transformations in `sql/`, orchestration in `src/pipeline.py`, and dashboard presentation in `app/`.

