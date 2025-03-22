# Generic Makefile for docker-compose service management

# Automatically get service name from the directory
SERVICE_NAME := $(shell basename $(CURDIR))

.PHONY: help start stop restart logs clean migrate migrate-status migrate-down client

# Default target shows help
help:
	@echo "$(SERVICE_NAME) Docker Environment"
	@echo ""
	@echo "Available commands:"
	@echo "  make start          - Start all $(SERVICE_NAME) services"
	@echo "  make stop           - Stop all $(SERVICE_NAME) services"
	@echo "  make restart        - Restart all $(SERVICE_NAME) services"
	@echo "  make logs           - View logs from all services"
	@echo "  make clean          - Remove all containers, networks, and volumes"
	@echo "  make migrate        - Run database migrations up"
	@echo "  make migrate-status - Check migration status"
	@echo "  make migrate-down   - Rollback the latest migration"
	@echo "  make client         - Connect to ClickHouse client"

# Start all services
start:
	@echo "Starting $(SERVICE_NAME) services..."
	docker compose up -d
	@echo "Services started in background. Use 'make logs' to view logs."

# Stop all services
stop:
	@echo "Stopping $(SERVICE_NAME) services..."
	docker compose down
	@echo "Services stopped."

# Restart all services
restart: stop start

# View logs
logs:
	docker compose logs -f

# Clean everything
clean:
	@echo "Removing all $(SERVICE_NAME) containers, networks, and volumes..."
	docker compose down -v
	@echo "Cleanup complete."

# Run migrations up
migrate:
	@echo "Running migrations..."
	@echo "Ensuring ClickHouse is ready..."
	@docker compose exec -T clickhouse wget --spider --quiet http://localhost:8123/ping || (echo "ClickHouse is not ready" && exit 1)
	@echo "ClickHouse is ready, running migrations..."
	docker compose run --rm migrations up
	@echo "Migrations complete."

# Check migration status
migrate-status:
	docker compose run --rm migrations status

# Rollback the latest migration
migrate-down:
	docker compose run --rm migrations down

# Connect to ClickHouse client
client:
	@echo "Connecting to ClickHouse client..."
	docker compose exec clickhouse clickhouse-client --host localhost
