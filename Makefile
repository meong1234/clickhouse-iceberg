# Main Makefile to control all services

# List all service directories
SERVICES := minio iceberg clickhouse

.PHONY: help start stop restart logs clean $(SERVICES) all-logs init-network

# Default target shows help
help:
	@echo "Main Control Makefile for All Services"
	@echo ""
	@echo "Available commands:"
	@echo "  make start         - Start all services"
	@echo "  make stop          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs from all services"
	@echo "  make clean         - Clean up all services"
	@echo "  make init-network  - Initialize the shared Docker network"
	@echo ""
	@echo "Service-specific commands:"
	@echo "  make iceberg       - Show iceberg service help"
	@echo "  make minio         - Show minio service help"
	@echo "  make clickhouse    - Show clickhouse service help"
	@echo ""
	@echo "  make iceberg-start - Start only iceberg service"
	@echo "  make minio-start      - Start only minio service"
	@echo "  make clickhouse-start - Start only clickhouse service"
	@echo "  (etc. for other actions: stop, restart, logs, clean)"

# Initialize the shared network
init-network:
	@echo "Initializing shared network..."
	@docker network inspect iceberg_network >/dev/null 2>&1 || docker network create iceberg_network
	@echo "Shared network 'iceberg_network' is ready"

# Start all services
start: init-network
	@echo "Starting all services..."
	@for service in $(SERVICES); do \
		echo "Starting $$service..."; \
		$(MAKE) -C $$service start; \
	done
	@echo "All services started."

# Stop all services
stop:
	@echo "Stopping all services..."
	@for service in $(SERVICES); do \
		echo "Stopping $$service..."; \
		$(MAKE) -C $$service stop; \
	done
	@echo "All services stopped."

# Restart all services
restart: stop start

# Clean everything
clean:
	@echo "Cleaning all services..."
	@for service in $(SERVICES); do \
		echo "Cleaning $$service..."; \
		$(MAKE) -C $$service clean; \
	done
	@echo "All services cleaned."

# Show all logs
all-logs:
	@echo "Viewing logs from all services is not recommended."
	@echo "Use make SERVICE-logs to view logs for a specific service."

# Service-specific targets
$(SERVICES):
	@$(MAKE) -C $@ help

# Generate service-specific action targets
define SERVICE_template
$(1)-start: init-network
	@$(MAKE) -C $(1) start

$(1)-stop:
	@$(MAKE) -C $(1) stop

$(1)-restart: init-network
	@$(MAKE) -C $(1) restart

$(1)-logs:
	@$(MAKE) -C $(1) logs

$(1)-clean:
	@$(MAKE) -C $(1) clean
endef

$(foreach service,$(SERVICES),$(eval $(call SERVICE_template,$(service))))