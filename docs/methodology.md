# Methodology

## Data Validation

Validation is rule based and checks uniqueness, nulls, referential integrity, positive quantities, non-negative cost and inventory values, date ordering, approved categories, score ranges, duplicate records, and extreme shipping cost values.

## Cleaning

Cleaning is deterministic. Duplicate shipments are removed, missing carriers are assigned `Unknown`, unsupported transport modes are mapped to `Truck`, invalid negative quantity or cost records are rejected, score fields are clipped to valid ranges, and extreme shipping costs are capped at a configurable quantile.

## Late Delivery Prediction

The target is `late_delivery_flag`. The split is time based to simulate future scoring. Features are limited to information available before delivery. Logistic regression is the interpretable baseline, and random forest is the advanced model. The selected model balances recall and precision-recall AUC because missed late deliveries are operationally costly.

## Forecasting

Demand is aggregated weekly by product category. The project evaluates naive, seasonal naive, and histogram gradient boosting forecasts with MAE, RMSE, WMAPE, MAPE, and forecast bias. The final forecast horizon is twelve weeks with approximate 80 percent intervals based on validation residuals.

## Inventory Optimization

For each product and warehouse, the module estimates demand mean, demand variability, lead time, lead-time variability, safety stock, reorder point, EOQ, recommended order quantity, stockout risk, carrying cost, and potential weekly savings.

## Shipment Allocation Optimization

The allocation model uses SciPy linear programming to recommend carrier-mode-priority allocation under capacity constraints. The objective penalizes cost and reliability risk. This is intentionally narrower than full vehicle routing to remain stable and interpretable.

