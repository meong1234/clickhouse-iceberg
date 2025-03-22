# Generic Makefile for docker-compose service management

# Automatically get service name from the directory
SERVICE_NAME := $(shell basename $(CURDIR))

.PHONY: help start stop restart logs clean

# Default target shows help
help:
	@echo "$(SERVICE_NAME) Docker Environment"
	@echo ""
	@echo "Available commands:"
	@echo "  make start    - Start all $(SERVICE_NAME) services"
	@echo "  make stop     - Stop all $(SERVICE_NAME) services"
	@echo "  make restart  - Restart all $(SERVICE_NAME) services"
	@echo "  make logs     - View logs from all services"
	@echo "  make clean    - Remove all containers, networks, and volumes"

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
