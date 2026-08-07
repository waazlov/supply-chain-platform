"""Demand forecasting at weekly product-category grain."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from src.evaluation import regression_metrics
from src.utils import write_json


def _weekly_category_demand(shipments: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    df = shipments.merge(products[["product_id", "product_category", "intermittent_demand_flag"]], on="product_id", how="left")
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["week_start"] = df["order_date"].dt.to_period("W").dt.start_time
    return df.groupby(["week_start", "product_category"], as_index=False).agg(
        demand_units=("quantity", "sum"),
        intermittent_share=("intermittent_demand_flag", "mean"),
    )


def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["week_of_year"] = out["week_start"].dt.isocalendar().week.astype(int)
    out["month"] = out["week_start"].dt.month
    out["time_index"] = ((out["week_start"] - out["week_start"].min()).dt.days // 7).astype(int)
    return pd.get_dummies(out, columns=["product_category"], drop_first=False)


def train_demand_forecasts(tables: dict[str, pd.DataFrame], config: dict[str, Any], output_dir: Path, model_dir: Path) -> dict[str, Any]:
    """Evaluate baselines and train a simple ML demand forecasting model."""
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    weekly = _weekly_category_demand(tables["shipments"], tables["products"])
    eval_weeks = int(config["forecasting"]["evaluation_weeks"])
    cutoff = weekly["week_start"].max() - pd.Timedelta(weeks=eval_weeks)
    train = weekly[weekly["week_start"] <= cutoff].copy()
    test = weekly[weekly["week_start"] > cutoff].copy()
    test = test.sort_values(["product_category", "week_start"])
    train_means = train.groupby("product_category")["demand_units"].mean()
    last_observed = train.sort_values("week_start").groupby("product_category")["demand_units"].last()
    seasonal = train.sort_values("week_start").groupby("product_category")["demand_units"].apply(lambda s: s.tail(52).mean())
    test["naive_forecast"] = test["product_category"].map(last_observed)
    test["seasonal_naive_forecast"] = test["product_category"].map(seasonal).fillna(test["product_category"].map(train_means))

    train_x = _add_time_features(train)
    test_x = _add_time_features(test)
    feature_cols = [col for col in train_x.columns if col not in ["week_start", "demand_units"]]
    for col in feature_cols:
        if col not in test_x:
            test_x[col] = 0
    model = HistGradientBoostingRegressor(max_iter=180, learning_rate=0.06, random_state=int(config["random_seed"]))
    model.fit(train_x[feature_cols], train_x["demand_units"])
    test["ml_forecast"] = np.maximum(0, model.predict(test_x[feature_cols])).round(0)

    metrics = {
        "naive": regression_metrics(test["demand_units"], test["naive_forecast"]),
        "seasonal_naive": regression_metrics(test["demand_units"], test["seasonal_naive_forecast"]),
        "hist_gradient_boosting": regression_metrics(test["demand_units"], test["ml_forecast"]),
    }
    horizon = int(config["forecasting"]["horizon_weeks"])
    future_rows = []
    for category in weekly["product_category"].unique():
        last_week = weekly["week_start"].max()
        for i in range(1, horizon + 1):
            future_rows.append({"week_start": last_week + pd.Timedelta(weeks=i), "product_category": category, "demand_units": np.nan, "intermittent_share": weekly.loc[weekly["product_category"].eq(category), "intermittent_share"].mean()})
    future = pd.DataFrame(future_rows)
    future_x = _add_time_features(future)
    for col in feature_cols:
        if col not in future_x:
            future_x[col] = 0
    future["forecast_units"] = np.maximum(0, model.predict(future_x[feature_cols])).round(0)
    residual_std = (test["demand_units"] - test["ml_forecast"]).std()
    future["lower_80"] = np.maximum(0, future["forecast_units"] - 1.28 * residual_std).round(0)
    future["upper_80"] = (future["forecast_units"] + 1.28 * residual_std).round(0)
    sparse = weekly.groupby("product_category").agg(avg_weekly_demand=("demand_units", "mean"), zero_like_weeks=("demand_units", lambda s: int((s < s.quantile(0.1)).sum())))
    future = future.merge(sparse.reset_index(), on="product_category", how="left")
    future["demand_stability"] = np.where(future["avg_weekly_demand"] < future["avg_weekly_demand"].median() * 0.55, "Sparse or intermittent", "Stable")
    weekly.to_csv(output_dir / "weekly_category_demand.csv", index=False)
    test.to_csv(output_dir / "forecast_evaluation.csv", index=False)
    future.to_csv(output_dir / "demand_forecast.csv", index=False)
    write_json(metrics, model_dir / "forecast_metrics.json")
    return metrics

