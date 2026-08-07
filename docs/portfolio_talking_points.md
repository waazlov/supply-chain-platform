# Portfolio Talking Points

## What problem does this project solve?

It helps a logistics company identify operational delay and cost drivers, predict late shipments, forecast demand, recommend inventory policies, and optimize carrier-mode allocation.

## Why did you choose this architecture?

The architecture separates ingestion, validation, transformation, modeling, optimization, and presentation. DuckDB and SQL handle analytical transformations, while Python handles orchestration, machine learning, forecasting, and optimization.

## How did you prevent target leakage?

The late-delivery model excludes fields only known after delivery, such as actual delivery date, actual transit days, delay days, and shipment status. It uses pre-delivery operational features only.

## Why did you use a time based split?

Supply chain models are used to score future shipments. A time-based split better represents production use than a random split and reduces overly optimistic evaluation.

## How did you validate the data?

The validation layer checks primary keys, required fields, foreign keys, business rules, categories, date ordering, score ranges, duplicate records, and outliers. It writes CSV and HTML quality reports.

## How did you evaluate the model?

The classifier is evaluated with accuracy, precision, recall, F1, ROC AUC, PR AUC, and a confusion matrix. Recall receives meaningful weight because missed late shipments can be costly.

## How does the optimization work?

Inventory optimization uses safety stock, reorder point, and EOQ formulas. Shipment allocation uses linear programming to minimize cost adjusted for reliability risk while respecting carrier-mode capacity.

## What business value could the project create?

It can reduce avoidable delay costs, improve carrier and supplier accountability, lower stockout risk, and support more disciplined inventory decisions.

## What limitations does this project have?

The default dataset is synthetic, allocation is aggregate rather than vehicle-route level, and cost assumptions need validation with finance and operations teams before real use.

## What would you improve with real company data?

Add ERP, WMS, TMS, weather, carrier contract, labor schedule, and customer SLA data. Then add model monitoring, data lineage, alert workflows, and lane-level optimization.

