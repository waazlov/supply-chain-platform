"""Late delivery prediction model training and scoring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import plotly.express as px
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.evaluation import classification_metrics
from src.feature_engineering import build_model_frame
from src.utils import write_json


NUMERIC_FEATURES = [
    "distance_km", "shipping_cost", "fuel_cost", "quantity", "unit_price", "inventory_level",
    "reorder_point", "supplier_lead_time_days", "warehouse_processing_hours", "weather_severity",
    "route_congestion_score", "expected_transit_days", "order_day_of_week", "inventory_gap",
    "reliability_score", "route_capacity_per_week", "intermittent_demand_flag",
]
CATEGORICAL_FEATURES = [
    "supplier_id", "warehouse_id", "carrier", "transport_mode", "priority_level", "product_category", "route_id",
]


def _preprocessor(scale_numeric: bool) -> ColumnTransformer:
    num_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        num_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer([
        ("num", Pipeline(num_steps), NUMERIC_FEATURES),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), CATEGORICAL_FEATURES),
    ])


def _time_split(df: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered = df.sort_values("order_date").copy()
    max_date = pd.to_datetime(ordered["order_date"]).max()
    test_start = max_date - pd.DateOffset(months=int(config["modeling"]["test_months"]))
    val_start = test_start - pd.DateOffset(months=int(config["modeling"]["validation_months"]))
    train = ordered[pd.to_datetime(ordered["order_date"]) < val_start]
    val = ordered[(pd.to_datetime(ordered["order_date"]) >= val_start) & (pd.to_datetime(ordered["order_date"]) < test_start)]
    test = ordered[pd.to_datetime(ordered["order_date"]) >= test_start]
    return train, val, test


def train_late_delivery_model(tables: dict[str, pd.DataFrame], config: dict[str, Any], model_dir: Path, report_dir: Path) -> dict[str, Any]:
    """Train baseline and advanced late delivery classifiers with leakage-safe features."""
    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    df = build_model_frame(tables["shipments"], tables["products"], tables["suppliers"], tables["routes"])
    train, val, test = _time_split(df, config)
    X_train, y_train = train[NUMERIC_FEATURES + CATEGORICAL_FEATURES], train["late_delivery_flag"]
    X_val, y_val = val[NUMERIC_FEATURES + CATEGORICAL_FEATURES], val["late_delivery_flag"]
    X_test, y_test = test[NUMERIC_FEATURES + CATEGORICAL_FEATURES], test["late_delivery_flag"]
    models = {
        "logistic_regression": Pipeline([
            ("prep", _preprocessor(scale_numeric=True)),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]),
        "random_forest": Pipeline([
            ("prep", _preprocessor(scale_numeric=False)),
            ("model", RandomForestClassifier(
                n_estimators=int(config["modeling"]["random_forest_estimators"]),
                min_samples_leaf=12,
                class_weight="balanced_subsample",
                random_state=int(config["random_seed"]),
                n_jobs=-1,
            )),
        ]),
    }
    validation_metrics = {}
    for name, pipe in models.items():
        pipe.fit(X_train, y_train)
        validation_metrics[name] = classification_metrics(y_val, pipe.predict_proba(X_val)[:, 1])
    recall_weight = float(config["modeling"]["late_recall_weight"])
    selected_name = max(
        validation_metrics,
        key=lambda name: recall_weight * validation_metrics[name]["recall"] + (1 - recall_weight) * validation_metrics[name]["pr_auc"],
    )
    final_model = models[selected_name]
    test_prob = final_model.predict_proba(X_test)[:, 1]
    test_metrics = classification_metrics(y_test, test_prob)

    scored = test[["shipment_id", "order_date", "carrier", "transport_mode", "priority_level", "late_delivery_flag"]].copy()
    scored["late_probability"] = test_prob
    scored.to_csv(report_dir / "late_delivery_scored_shipments.csv", index=False)
    joblib.dump(final_model, model_dir / "late_delivery_model.joblib")
    feature_metadata = {"numeric_features": NUMERIC_FEATURES, "categorical_features": CATEGORICAL_FEATURES, "selected_model": selected_name}
    write_json(feature_metadata, model_dir / "late_delivery_feature_metadata.json")
    metrics = {"validation": validation_metrics, "test": test_metrics, "selected_model": selected_name, "test_rows": int(len(test))}
    write_json(metrics, model_dir / "late_delivery_metrics.json")

    cm = pd.DataFrame(test_metrics["confusion_matrix"], index=["Actual on time", "Actual late"], columns=["Predicted on time", "Predicted late"])
    px.imshow(cm, text_auto=True, title="Late Delivery Confusion Matrix").write_html(report_dir / "late_delivery_confusion_matrix.html")
    # Save lightweight model-performance datasets for dashboard use.
    pd.DataFrame([test_metrics]).drop(columns=["confusion_matrix"]).to_csv(report_dir / "late_delivery_metrics.csv", index=False)
    model_card = _model_card(selected_name, metrics, feature_metadata)
    (report_dir / "model_card.md").write_text(model_card, encoding="utf-8")
    return metrics


def _model_card(selected_name: str, metrics: dict[str, Any], feature_metadata: dict[str, Any]) -> str:
    return f"""# Late Delivery Prediction Model Card

## Intended use
Prioritize shipments for proactive operations review before delivery occurs.

## Selected model
{selected_name}

## Training data
Synthetic but relational shipment, order, route, supplier, product, and warehouse data generated with a fixed seed. The split is time based to simulate future scoring.

## Leakage prevention
The model uses only fields available before delivery, including order, routing, supplier, inventory, priority, distance, cost estimate, weather, and congestion features. Actual delivery date, actual transit days, delay days, and shipment status are excluded.

## Test metrics
- Accuracy: {metrics["test"]["accuracy"]:.3f}
- Precision: {metrics["test"]["precision"]:.3f}
- Recall: {metrics["test"]["recall"]:.3f}
- F1: {metrics["test"]["f1"]:.3f}
- ROC AUC: {metrics["test"]["roc_auc"]:.3f}
- PR AUC: {metrics["test"]["pr_auc"]:.3f}

## Limitations
Synthetic data cannot represent all operational constraints, carrier contract terms, or real-world data quality issues. Model results should be recalibrated with live historical data before operational use.

## Feature groups
Numeric: {", ".join(feature_metadata["numeric_features"])}

Categorical: {", ".join(feature_metadata["categorical_features"])}
"""
