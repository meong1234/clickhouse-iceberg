SET allow_experimental_database_iceberg = 1;

DROP DATABASE IF EXISTS iceberg_catalog;

CREATE DATABASE iceberg_catalog
ENGINE = DataLakeCatalog('http://iceberg-catalog:8181', 'minio-root-user', 'minio-root-password')
SETTINGS 
    catalog_type = 'rest', 
    warehouse = 'warehouse', 
    storage_endpoint = 'http://minio:9000/warehouse';
    

SHOW TABLES FROM iceberg_catalog;    

use iceberg_catalog;

SHOW CREATE TABLE iceberg_catalog.`iot_battery.battery_v2`;

-- Basic query to see all data
SELECT * FROM iceberg_catalog.`iot_battery.battery_v2`;

-- Query showing battery telemetry sorted by time
SELECT 
  event_time,
  battery_serial,
  state_of_charge,
  state_of_health,
  charge_cycles 
FROM iceberg_catalog.`iot_battery.battery_v2`
ORDER BY event_time DESC
LIMIT 10;

-- Query focusing on specific batteries
SELECT 
  event_time,
  battery_serial,
  state_of_charge,
  state_of_health,
  charge_cycles 
FROM iceberg_catalog.`iot_battery.battery_v2`
WHERE battery_serial IN ('battery-01', 'battery-02')
ORDER BY event_time DESC;

-- Query for recent battery data
SELECT 
  event_time,
  battery_serial,
  state_of_charge,
  state_of_health,
  charge_cycles 
FROM iceberg_catalog.`iot_battery.battery_v2`
WHERE event_time >= now() - INTERVAL 7 DAY
ORDER BY event_time DESC;

-- Show table structure
DESCRIBE TABLE iceberg_catalog.`iot_battery.battery_v2`;

