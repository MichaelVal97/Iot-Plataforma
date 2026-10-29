SELECT 'dim_sensors' AS tabla, COUNT(*) AS filas
FROM `iot-warehouse-512323.iot_warehouse.dim_sensors`
UNION ALL
SELECT 'fact_readings', COUNT(*)
FROM `iot-warehouse-512323.iot_warehouse.fact_readings`;
