# ClickHouse Iceberg Catalog Integration

[![ClickHouse](https://img.shields.io/badge/ClickHouse-v25.3+-00AFD7?style=flat-square&logo=clickhouse&logoColor=white)](https://clickhouse.com/)
[![Apache Iceberg](https://img.shields.io/badge/Apache_Iceberg-Latest-3371e3?style=flat-square&logo=apache&logoColor=white)](https://iceberg.apache.org/)
[![MinIO](https://img.shields.io/badge/MinIO-S3_Compatible-C72C48?style=flat-square&logo=minio&logoColor=white)](https://min.io/)

## Table of Contents
- [Overview](#overview)
- [Key Benefits](#key-benefits)
- [Components and Architecture](#components-and-architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Accessing Services](#accessing-services)
- [Using the Integration](#using-the-integration)
  - [Creating the Iceberg Database](#creating-the-iceberg-database-in-clickhouse)
  - [Exploring Available Tables](#exploring-available-tables)
  - [Querying Iceberg Tables](#querying-iceberg-tables)
  - [Understanding Table Structure](#understanding-table-structure)
- [Implementing Hot/Cold Data Strategy](#implementing-hotcold-data-strategy)
- [Project Structure](#project-structure)
  - [Directory Layout](#directory-structure)
  - [Component Details](#detailed-component-information)
  - [Makefile Commands](#makefile-commands)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)
- [References](#references)
- [License](#license)

## Overview

This project demonstrates how to integrate ClickHouse with Apache Iceberg tables using ClickHouse's DataLakeCatalog connector. It provides a complete end-to-end setup where you can query and analyze data stored in Iceberg tables directly from ClickHouse without any ETL processes.

![ClickHouse Iceberg Integration](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*H_zQYYiSG1ZeQXGu52Ty8Q.png)

### What is this project about?

- **Apache Iceberg**: An open table format for huge analytic datasets
- **ClickHouse**: A high-performance columnar database
- **Integration**: ClickHouse connecting to Iceberg tables through DataLakeCatalog

> **Note:** This integration uses ClickHouse version 25.3 or later. The DataLakeCatalog feature is marked as experimental in these versions.

## Key Benefits

- **Cost Optimization**: Store historical or cold data in object storage (S3/MinIO) while maintaining query capabilities
- **Query Federation**: Use ClickHouse's powerful analytics on both hot data (in ClickHouse native tables) and cold data (in Iceberg)
- **Unified Data Access**: Query across multiple storage tiers with a single interface

## Components and Architecture

This project sets up a Docker-based environment with the following components:

1. **ClickHouse Server**: Database engine for querying Iceberg data
2. **Iceberg REST Catalog**: HTTP service for managing Iceberg metadata (using [tabulario/iceberg-rest](https://github.com/tabulario/iceberg-rest))
3. **MinIO**: S3-compatible object storage for the actual data files
4. **Python Utilities**: Tools for schema creation and data generation

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│       ┌───────────────┐       ┌────────────────┐                │
│       │  ClickHouse   │       │ Iceberg REST   │                │
│       │   Server      │───────│   Catalog      │                │
│       └───────────────┘       └────────────────┘                │
│              │                         │                        │
│              │                         │                        │
│              │                         │                        │
│              │                         ▼                        │
│              │                ┌────────────────┐                │
│              │                │    MinIO/S3    │                │
│              │                │  Object Store  │                │
│              │                └────────────────┘                │
│              │                         ▲                        │
│              │                         │                        │
│              └─────────────────────────┘                        │
│                  Direct data access                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Make (optional but recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourname/clickhouse-iceberg.git
   cd clickhouse-iceberg
   ```

2. **Start all services**:
   ```bash
   make start
   ```
   
   This will start ClickHouse, Iceberg REST Catalog, and MinIO services.

3. **Check service status**:
   ```bash
   docker ps
   ```

4. **Wait for initialization** (services may take a minute to fully initialize)

### Accessing Services

| Service | Access Method | URL/Port |
|---------|---------------|----------|
| ClickHouse | CLI Client | `make clickhouse-client` |
| ClickHouse HTTP | Browser/curl | http://localhost:8123 |
| MinIO Console | Browser | http://localhost:9001 (login: minio-root-user/minio-root-password) |
| Iceberg REST API | HTTP | http://localhost:8181 |

## Using the Integration

### Creating the Iceberg Database in ClickHouse

Once connected to ClickHouse, create a database connection to Iceberg:

```sql
-- Enable experimental feature first
SET allow_experimental_database_iceberg = 1;

-- Create connection to Iceberg catalog
CREATE DATABASE iceberg_catalog
ENGINE = DataLakeCatalog('http://iceberg-catalog:8181', 'minio-root-user', 'minio-root-password')
SETTINGS 
    catalog_type = 'rest', 
    warehouse = 'warehouse', 
    storage_endpoint = 'http://minio:9000/warehouse';
```

### Exploring Available Tables

```sql
-- List available tables in the Iceberg catalog
SHOW TABLES FROM iceberg_catalog;
```

### Querying Iceberg Tables

```sql
-- Basic query
SELECT * FROM iceberg_catalog.`iot_battery.battery_v2` LIMIT 10;

-- Structured query with filters
SELECT 
  event_time,
  battery_serial,
  state_of_charge,
  state_of_health
FROM iceberg_catalog.`iot_battery.battery_v2`
WHERE battery_serial = 'battery-01'
  AND event_time >= now() - INTERVAL 1 DAY
ORDER BY event_time DESC;
```

### Understanding Table Structure

```sql
-- View table schema
DESCRIBE TABLE iceberg_catalog.`iot_battery.battery_v2`;

-- Show table creation statement
SHOW CREATE TABLE iceberg_catalog.`iot_battery.battery_v2`;
```

## Project Structure

### Directory Structure

```
clickhouse-iceberg/
├── Makefile                      # Main control file
├── clickhouse/                   # ClickHouse configuration
│   ├── Makefile                  # ClickHouse service commands
│   ├── config/                   # Server config
│   ├── docker-compose.yaml       # ClickHouse service definition
│   ├── how_query.sql             # Example queries
│   ├── migrations/               # SQL migrations
│   │   └── 00004_create_lakekeeper_catalog.sql
│   └── users/                    # User settings
├── iceberg/                      # Iceberg catalog service
│   ├── docker-compose.yaml       # Iceberg service definition
│   └── python/                   # Schema creation scripts
│       ├── Dockerfile            # Python environment for Iceberg tools
│       └── create_battery_schema.py # Data creation script
├── minio/                        # MinIO configuration
│   └── docker-compose.yaml       # MinIO service definition
└── data/                         # Persistent data storage
    ├── clickhouse/               # ClickHouse data files
    ├── iceberg/                  # Iceberg metadata logs
    └── minio/                    # MinIO object storage data
```

### Detailed Component Information

#### 1. ClickHouse Configuration

The ClickHouse server is configured with:
- HTTP interface on port 8123
- Native protocol on port 9000
- Custom configurations in the `./clickhouse/config` directory
- Database migrations in `./clickhouse/migrations`

**Key Configuration Files:**
- `users.xml`: Authentication and user permissions
- `config.xml`: Server configuration settings

#### 2. Iceberg REST Catalog

The Iceberg REST Catalog provides:
- Based on [tabulario/iceberg-rest](https://github.com/tabulario/iceberg-rest)
- HTTP API on port 8181
- Manages Iceberg table metadata
- Connects to MinIO for storage
- Configured to use the 'warehouse' bucket

**REST Endpoints:**
- `GET /v1/namespaces`: List available namespaces
- `GET /v1/namespaces/{namespace}/tables`: List tables in a namespace
- `GET /v1/namespaces/{namespace}/tables/{table}`: Get table metadata

#### 3. MinIO Object Storage

MinIO provides:
- S3-compatible storage on port 9002
- Web console on port 9001 (login with `minio-root-user`/`minio-root-password`)
- Stores actual data files in Parquet format
- Configured with user 'minio-root-user'

**Key Buckets:**
- `warehouse`: Main storage for Iceberg data files
- Access via browser at http://localhost:9001

#### 4. Sample Data

The project includes a sample IoT battery dataset with:

# View logs for specific service
make iceberg-logs
make minio-logs
make clickhouse-logs
```

## Troubleshooting

### Common Issues

1. **Services not starting properly**
   - Check Docker logs: `docker logs clickhouse-server`
   - Ensure no port conflicts with existing services
   - Check network connectivity between containers: `docker network inspect iceberg_network`

2. **Cannot connect to ClickHouse**
   - Verify ClickHouse is running: `docker ps | grep clickhouse`
   - Check if ports are exposed correctly: `netstat -tuln | grep 8123`
   - Try connecting directly to container: `docker exec -it clickhouse-server clickhouse-client`

3. **Tables not appearing in Iceberg catalog**
   - Ensure the Iceberg REST service is healthy: `curl http://localhost:8181/v1/namespaces`
   - Check MinIO is accessible and the warehouse bucket exists
   - Review Iceberg schema creation logs: `docker logs iceberg-catalog`

4. **"Database not found" errors**
   - Ensure the experimental flag is enabled: `SET allow_experimental_database_iceberg = 1;`
   - Check catalog connection parameters
   - Verify MinIO credentials are correct

### Logs

- **ClickHouse logs**: `make clickhouse-logs`
- **Iceberg catalog logs**: `docker logs iceberg-catalog`
- **MinIO logs**: `docker logs minio`
- **Schema creation logs**: Check the files in `./data/iceberg/schema-logs/`

## Advanced Topics

### Extending the Schema

To create additional tables in the Iceberg catalog, modify the Python schema creation script:
`./iceberg/python/create_battery_schema.py`

Example:
```python
# Define a new schema for vehicle data
vehicle_schema = Schema(
    NestedField(1, "vehicle_id", StringType(), required=True),
    NestedField(2, "timestamp", TimestampType(), required=True),
    NestedField(3, "speed", DoubleType(), required=False),
    NestedField(4, "location", StringType(), required=False)
)

# Create the table
catalog.create_table(
    identifier=f"{namespace}.vehicles",
    schema=vehicle_schema,
    partition_spec=PartitionSpec()
)
```

### Performance Tuning

For larger datasets:
- **Partitioning**: Add appropriate partitioning to Iceberg tables
  ```python
  # Partition by day for time-series data
  partition_spec = PartitionSpec(
      PartitionField(source_id=1, field_id=100, transform=DayTransform(), name="event_day")
  )
  ```


## References

- [ClickHouse Documentation](https://clickhouse.com/docs)
- [ClickHouse Data Lake Connector](https://clickhouse.com/docs/en/databases/datalake_catalog)
- [Apache Iceberg Documentation](https://iceberg.apache.org/)
- [Iceberg REST Catalog API](https://iceberg.apache.org/docs/latest/api/#rest-catalog)
- [tabulario/iceberg-rest](https://github.com/tabulario/iceberg-rest)
- [MinIO Documentation](https://docs.min.io/)
- [PyIceberg Documentation](https://py.iceberg.apache.org/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

