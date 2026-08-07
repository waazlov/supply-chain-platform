CREATE OR REPLACE TABLE shipment_performance_summary AS
WITH enriched AS (
    SELECT
        sf.*,
        p.product_category,
        c.customer_region
    FROM shipment_features sf
    LEFT JOIN products p USING (product_id)
    LEFT JOIN customers c USING (customer_id)
)
SELECT
    order_month,
    product_category,
    carrier,
    transport_mode,
    priority_level,
    customer_region,
    COUNT(*) AS shipment_count,
    AVG(1 - late_delivery_flag) AS on_time_delivery_rate,
    AVG(delay_days) AS average_delay_days,
    SUM(shipping_cost) AS total_shipping_cost,
    AVG(shipping_cost) AS average_shipping_cost,
    AVG(cost_per_km) AS cost_per_km,
    AVG(cost_per_unit) AS cost_per_unit,
    AVG(order_cycle_time_days) AS order_cycle_time_days,
    SUM(delay_cost_estimate) AS estimated_delay_cost,
    SUM(stockout_cost_estimate) AS lost_sales_estimate
FROM enriched
GROUP BY 1,2,3,4,5,6;

CREATE OR REPLACE TABLE supplier_scorecard AS
WITH base AS (
    SELECT
        s.supplier_id,
        sup.supplier_name,
        sup.supplier_region,
        COUNT(*) AS shipment_count,
        AVG(1 - s.late_delivery_flag) AS on_time_delivery_rate,
        AVG(s.delay_days) AS average_delay_days,
        AVG(s.defect_flag) AS supplier_defect_rate,
        AVG(s.supplier_lead_time_days) AS supplier_average_lead_time,
        SUM(s.delay_cost_estimate) AS estimated_delay_cost,
        SUM(s.stockout_flag) AS stockout_shipments
    FROM shipment_features s
    LEFT JOIN suppliers sup USING (supplier_id)
    GROUP BY 1,2,3
)
SELECT
    *,
    RANK() OVER (ORDER BY supplier_defect_rate DESC, average_delay_days DESC) AS defect_delay_rank,
    (0.45 * (1 - on_time_delivery_rate) + 0.35 * supplier_defect_rate + 0.20 * stockout_shipments / NULLIF(shipment_count, 0)) AS supplier_risk_score
FROM base;

CREATE OR REPLACE TABLE carrier_performance_scorecard AS
WITH carrier_base AS (
    SELECT
        carrier,
        transport_mode,
        COUNT(*) AS shipment_count,
        AVG(1 - late_delivery_flag) AS on_time_delivery_rate,
        AVG(delay_days) AS average_delay_days,
        AVG(shipping_cost) AS average_shipping_cost,
        AVG(cost_per_km) AS cost_per_km,
        AVG(CASE WHEN defect_flag = 0 AND late_delivery_flag = 0 AND stockout_flag = 0 THEN 1 ELSE 0 END) AS perfect_order_rate
    FROM shipment_features
    GROUP BY 1,2
)
SELECT
    *,
    (0.50 * on_time_delivery_rate + 0.30 * perfect_order_rate + 0.20 * (1 - LEAST(1, average_delay_days / 7))) AS carrier_reliability_score,
    RANK() OVER (ORDER BY average_shipping_cost ASC) AS cost_rank
FROM carrier_base;

CREATE OR REPLACE TABLE route_performance_summary AS
WITH route_base AS (
    SELECT
        sf.route_id,
        r.origin_region,
        r.destination_region,
        COUNT(*) AS shipment_count,
        AVG(sf.distance_km) AS average_distance_km,
        AVG(sf.route_congestion_score) AS average_congestion,
        AVG(1 - sf.late_delivery_flag) AS on_time_delivery_rate,
        AVG(sf.delay_days) AS average_delay_days,
        SUM(sf.shipping_cost) AS total_shipping_cost,
        AVG(sf.cost_per_km) AS cost_per_km,
        SUM(sf.delay_cost_estimate) AS estimated_delay_cost
    FROM shipment_features sf
    LEFT JOIN routes r USING (route_id)
    GROUP BY 1,2,3
)
SELECT
    *,
    (0.40 * average_congestion + 0.35 * (1 - on_time_delivery_rate) + 0.25 * LEAST(1, average_delay_days / 7)) AS route_risk_score,
    RANK() OVER (ORDER BY total_shipping_cost DESC) AS cost_rank
FROM route_base;

CREATE OR REPLACE TABLE warehouse_utilization_summary AS
WITH warehouse_base AS (
    SELECT
        sf.warehouse_id,
        w.warehouse_region,
        w.capacity_units,
        COUNT(*) AS shipment_count,
        SUM(sf.quantity) AS shipped_units,
        AVG(sf.warehouse_processing_hours) AS warehouse_processing_time,
        AVG(sf.route_congestion_score) AS average_congestion,
        AVG(sf.stockout_flag) AS stockout_rate,
        AVG(sf.inventory_level) AS average_inventory_level
    FROM shipment_features sf
    LEFT JOIN warehouses w USING (warehouse_id)
    GROUP BY 1,2,3
)
SELECT
    *,
    shipped_units / NULLIF(capacity_units, 0) AS capacity_utilization_ratio,
    RANK() OVER (ORDER BY warehouse_processing_time DESC) AS processing_time_rank
FROM warehouse_base;

CREATE OR REPLACE TABLE product_demand_summary AS
WITH product_orders AS (
    SELECT
        sf.product_id,
        p.product_category,
        sf.order_month,
        SUM(sf.quantity) AS demand_units,
        SUM(sf.quantity * sf.unit_price) AS demand_value,
        AVG(sf.stockout_flag) AS stockout_rate,
        AVG(sf.defect_flag) AS defect_rate
    FROM shipment_features sf
    LEFT JOIN products p USING (product_id)
    GROUP BY 1,2,3
)
SELECT
    *,
    demand_units - LAG(demand_units) OVER (PARTITION BY product_id ORDER BY order_month) AS demand_unit_change,
    AVG(demand_units) OVER (PARTITION BY product_id ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_3m_demand
FROM product_orders;

CREATE OR REPLACE TABLE inventory_risk_summary AS
WITH base AS (
    SELECT
        product_id,
        warehouse_id,
        COUNT(*) AS shipment_count,
        AVG(inventory_level) AS average_inventory,
        AVG(reorder_point) AS average_reorder_point,
        AVG(stockout_flag) AS stockout_rate,
        SUM(stockout_cost_estimate) AS lost_sales_estimate,
        AVG(quantity) AS average_order_quantity,
        AVG(unit_price) AS average_unit_price
    FROM shipment_features
    GROUP BY 1,2
)
SELECT
    *,
    average_inventory / NULLIF(average_order_quantity, 0) AS days_of_inventory_proxy,
    average_order_quantity * 52 / NULLIF(average_inventory, 0) AS inventory_turnover_proxy,
    GREATEST(0, average_inventory - average_reorder_point * 2) * average_unit_price AS excess_inventory_value,
    CASE
        WHEN stockout_rate >= 0.25 THEN 'High'
        WHEN stockout_rate >= 0.12 THEN 'Medium'
        ELSE 'Low'
    END AS inventory_risk_level
FROM base;

CREATE OR REPLACE TABLE monthly_logistics_cost_summary AS
SELECT
    order_month,
    COUNT(*) AS shipment_count,
    SUM(shipping_cost) AS total_shipping_cost,
    SUM(fuel_cost) AS total_fuel_cost,
    AVG(shipping_cost) AS average_shipping_cost_per_order,
    AVG(cost_per_km) AS average_cost_per_km,
    SUM(delay_cost_estimate) AS estimated_delay_cost,
    SUM(stockout_cost_estimate) AS lost_sales_estimate
FROM shipment_features
GROUP BY 1
ORDER BY 1;

CREATE OR REPLACE TABLE late_delivery_root_cause_summary AS
SELECT
    priority_level,
    transport_mode,
    carrier,
    CASE
        WHEN weather_severity >= 0.70 THEN 'Severe weather'
        WHEN route_congestion_score >= 0.75 THEN 'Route congestion'
        WHEN warehouse_processing_hours >= 36 THEN 'Warehouse processing'
        WHEN supplier_lead_time_days >= 20 THEN 'Supplier lead time'
        ELSE 'Mixed operational factors'
    END AS likely_driver,
    COUNT(*) AS shipment_count,
    AVG(late_delivery_flag) AS late_delivery_rate,
    AVG(delay_days) AS average_delay_days,
    AVG(weather_severity) AS average_weather_severity,
    AVG(route_congestion_score) AS average_route_congestion,
    AVG(warehouse_processing_hours) AS average_processing_hours,
    SUM(delay_cost_estimate) AS estimated_delay_cost
FROM shipment_features
GROUP BY 1,2,3,4
HAVING COUNT(*) >= 20;

CREATE OR REPLACE TABLE executive_kpi_summary AS
SELECT
    MIN(order_date) AS report_start_date,
    MAX(order_date) AS report_end_date,
    COUNT(*) AS total_shipments,
    AVG(1 - late_delivery_flag) AS on_time_delivery_rate,
    AVG(delay_days) AS average_delay_days,
    SUM(shipping_cost) AS total_logistics_cost,
    AVG(shipping_cost) AS average_shipping_cost_per_order,
    AVG(cost_per_km) AS cost_per_kilometer,
    AVG(CASE WHEN defect_flag = 0 AND late_delivery_flag = 0 AND stockout_flag = 0 THEN 1 ELSE 0 END) AS perfect_order_rate,
    AVG(stockout_flag) AS stockout_rate,
    AVG(defect_flag) AS defect_rate,
    SUM(delay_cost_estimate) AS estimated_delay_cost,
    SUM(stockout_cost_estimate) AS lost_sales_estimate,
    SUM(delay_cost_estimate + stockout_cost_estimate) AS estimated_financial_impact
FROM shipment_features;

