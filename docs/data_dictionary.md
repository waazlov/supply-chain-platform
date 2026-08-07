# Data Dictionary

## Core Tables

### shipments

Shipment-level operational fact table. Important fields include `shipment_id`, `order_id`, `product_id`, `supplier_id`, `warehouse_id`, `customer_id`, `route_id`, `carrier`, `transport_mode`, `order_date`, `ship_date`, `expected_delivery_date`, `actual_delivery_date`, `distance_km`, `shipping_cost`, `fuel_cost`, `quantity`, `unit_price`, `inventory_level`, `reorder_point`, `supplier_lead_time_days`, `warehouse_processing_hours`, `weather_severity`, `route_congestion_score`, `shipment_status`, `priority_level`, `defect_flag`, `stockout_flag`, and `late_delivery_flag`.

### orders

Order-level table with `order_id`, `customer_id`, `product_id`, `order_date`, `quantity`, `unit_price`, `order_value`, and `priority_level`.

### products

Product dimension with category, price, cost, shelf-life, and intermittent-demand indicator.

### suppliers

Supplier dimension with region, base lead time, defect rate, and reliability score.

### warehouses

Warehouse dimension with region, capacity, and labor shift count.

### customers

Customer dimension with region and segment.

### routes

Route dimension with origin, destination, default mode, distance, weekly capacity, and congestion score.

### inventory_snapshots

Weekly product-warehouse inventory levels and reorder points.

### purchase_orders

Supplier purchase order history with expected and actual receipt dates.

### calendar

Date dimension with year, month, week, quarter, and peak-season indicator.

## Derived Fields

- `delay_days`: Days after expected delivery date, clipped at zero.
- `cost_per_km`: Shipping cost divided by route distance.
- `cost_per_unit`: Shipping cost divided by shipped quantity.
- `inventory_gap`: Inventory level minus reorder point.
- `delay_cost_estimate`: Estimated financial impact from late deliveries.
- `stockout_cost_estimate`: Estimated lost-sales exposure from stockout flags.

