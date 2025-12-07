# ============================================================================
# ClickHouse + Iceberg + MinIO - Makefile
# ============================================================================

.PHONY: help up down restart logs ps clean network cli

# Default target
help:
	@echo "ClickHouse + Iceberg + MinIO Stack"
	@echo ""
	@echo "Usage:"
	@echo "  make up      - Start all services"
	@echo "  make down    - Stop all services"
	@echo "  make restart - Restart all services"
	@echo "  make logs    - View logs (follow mode)"
	@echo "  make ps      - Show running services"
	@echo "  make clean   - Stop and remove all data"
	@echo "  make cli     - Connect to ClickHouse client"
	@echo ""

# Create network if it doesn't exist
network:
	@docker network inspect iceberg_network >/dev/null 2>&1 || docker network create iceberg_network

# Start all services
up: network
	@docker compose up -d
	@echo ""
	@echo "Services started! Access points:"
	@echo "  - MinIO Console:    http://localhost:9001"
	@echo "  - MinIO API:        http://localhost:9002"
	@echo "  - Iceberg Catalog:  http://localhost:8181"
	@echo "  - ClickHouse HTTP:  http://localhost:8123"
	@echo "  - ClickHouse Native: localhost:9000"

# Stop all services
down:
	@docker compose down

# Restart all services
restart: down up

# View logs
logs:
	@docker compose logs -f

# Show running services
ps:
	@docker compose ps

# Connect to ClickHouse client
cli:
	@docker exec -it clickhouse-server clickhouse-client

# Stop and remove all data (use with caution)
clean:
	@echo "WARNING: This will remove all containers and data!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	@docker compose down -v
	@rm -rf ./data/minio/* ./data/clickhouse/*
	@echo "All data cleaned."