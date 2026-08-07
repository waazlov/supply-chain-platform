# Late Delivery Model Card

The pipeline writes the generated model card to `reports/model_card.md` after `python scripts/run_pipeline.py all`.

This source document describes the intended model governance structure:

- Intended use: prioritize shipments for proactive operations review.
- Not intended for: automated customer penalties, employee performance decisions, or carrier enforcement without human review.
- Training data: deterministic synthetic logistics data unless replaced by real source data.
- Split: time based train, validation, and test periods.
- Leakage controls: no actual delivery date, delay days, actual transit days, or shipment status in model features.
- Metrics: accuracy, precision, recall, F1, ROC AUC, PR AUC, confusion matrix, and segment performance opportunities.
- Limitations: synthetic data, simplified weather and congestion proxies, and no real contract constraints.

