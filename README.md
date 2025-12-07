# ClickHouse + Apache Iceberg Demo

A hands-on demo for **ClickHouse Meetup** showcasing ClickHouse with Apache Iceberg tables using the `IcebergS3` engine and MinIO for S3-compatible storage.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│     ┌─────────────────┐         ┌─────────────────┐     │
│     │   ClickHouse    │         │      MinIO      │     │
│     │   (IcebergS3)   │────────▶│  (S3 Storage)   │     │
│     └─────────────────┘         └─────────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Start all services
make up

# Connect to ClickHouse
make cli
```

## Services

| Service | URL | Credentials |
|---------|-----|-------------|
| ClickHouse HTTP | http://localhost:8123 | - |
| ClickHouse Native | localhost:9000 | - |
| MinIO Console | http://localhost:9001 | minio-root-user / minio-root-password |
| MinIO API | http://localhost:9002 | - |

---

## Tutorial

### 1. Enable Experimental Features

```sql
SET allow_experimental_database_iceberg = 1;
SET allow_experimental_insert_into_iceberg = 1;
SET output_format_parquet_use_custom_encoder = 0;
SET output_format_parquet_parallel_encoding = 0;
```

### 2. Create Iceberg Table

```sql
CREATE DATABASE IF NOT EXISTS iot_data;

CREATE TABLE IF NOT EXISTS iot_data.battery_telemetry
(
    event_time      DateTime,
    battery_serial  String,
    state_of_charge Float32,
    state_of_health Float32,
    charge_cycles   UInt32,
    temperature     Float32,
    voltage         Float32
)
ENGINE = IcebergS3(
    'http://minio:9000/warehouse/iot_data/battery_telemetry/',
    'minio-root-user',
    'minio-root-password'
)
SETTINGS iceberg_engine_ignore_schema_evolution = 1;
```

### 3. Insert Data

```sql
-- Single row (initializes the table)
INSERT INTO iot_data.battery_telemetry VALUES
    (now(), 'BAT-001', 85.5, 98.2, 150, 25.3, 3.7);

-- Multiple rows
INSERT INTO iot_data.battery_telemetry VALUES
    (now(), 'BAT-002', 72.1, 95.8, 220, 28.1, 3.6),
    (now(), 'BAT-003', 91.2, 99.1, 80, 23.5, 3.8),
    (now() - INTERVAL 1 HOUR, 'BAT-001', 87.2, 98.2, 150, 24.8, 3.7);

-- Generate sample data
INSERT INTO iot_data.battery_telemetry
SELECT
    now() - INTERVAL number MINUTE AS event_time,
    concat('BAT-', lpad(toString((number % 10) + 1), 3, '0')) AS battery_serial,
    50 + (rand() % 50) AS state_of_charge,
    90 + (rand() % 10) AS state_of_health,
    100 + (number % 500) AS charge_cycles,
    20 + (rand() % 15) AS temperature,
    3.5 + (rand() % 5) / 10.0 AS voltage
FROM numbers(100);
```

### 4. Query Data

```sql
-- Basic query
SELECT * FROM iot_data.battery_telemetry LIMIT 10;

-- Latest reading per battery
SELECT 
    battery_serial,
    max(event_time) AS last_seen,
    argMax(state_of_charge, event_time) AS current_soc,
    argMax(state_of_health, event_time) AS current_soh
FROM iot_data.battery_telemetry
GROUP BY battery_serial
ORDER BY battery_serial;

-- Time-based query
SELECT event_time, battery_serial, state_of_charge, temperature
FROM iot_data.battery_telemetry
WHERE event_time >= now() - INTERVAL 1 HOUR
ORDER BY event_time DESC;

-- Aggregations
SELECT 
    battery_serial,
    count() AS reading_count,
    round(avg(state_of_charge), 2) AS avg_soc,
    round(avg(temperature), 2) AS avg_temp,
    min(state_of_charge) AS min_soc,
    max(state_of_charge) AS max_soc
FROM iot_data.battery_telemetry
GROUP BY battery_serial
ORDER BY avg_soc DESC;
```

---

## Advanced Features

```

### Partition Pruning

```sql
SELECT * FROM iot_data.battery_telemetry
WHERE event_time >= '2024-01-01'
SETTINGS use_iceberg_partition_pruning = 1;
```

### Schema Evolution

ClickHouse supports reading Iceberg tables with evolved schemas:
- Adding/removing columns
- Changing column order
- Type casting (int → long, float → double, decimal precision changes)

### Metadata Cache

```sql
-- Disable cache if needed
SELECT * FROM iot_data.battery_telemetry
SETTINGS use_iceberg_metadata_files_cache = 0;
```

---

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | View logs (follow mode) |
| `make ps` | Show running services |
| `make cli` | Connect to ClickHouse client |
| `make clean` | Stop and remove all data |

## Project Structure

```
clickhouse-iceberg/
├── docker-compose.yaml       # Service definitions
├── Makefile                  # Task automation
├── clickhouse/
│   ├── config/               # Server configuration
│   └── users/                # User settings
└── data/
    ├── clickhouse/           # ClickHouse data
    └── minio/                # MinIO storage (Iceberg tables)
```

## Troubleshooting

```bash
# Check service status
make ps

# View logs
make logs

# Check MinIO contents
docker exec -it mc mc ls minio/warehouse --recursive
```

## References

- [ClickHouse Iceberg Documentation](https://clickhouse.com/docs/en/sql-reference/table-functions/iceberg)
- [ClickHouse IcebergS3 Engine](https://clickhouse.com/docs/en/engines/table-engines/integrations/iceberg)
- [Apache Iceberg](https://iceberg.apache.org/)
