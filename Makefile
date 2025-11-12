.PHONY: help build test run clean docker-up docker-down seed-redis

help:
	@echo "Available commands:"
	@echo "  make docker-up      - Start Redis container"
	@echo "  make docker-down    - Stop Redis container"
	@echo "  make seed-redis     - Seed Redis with sample data"
	@echo "  make build          - Build all components"
	@echo "  make test           - Run all tests"
	@echo "  make clean          - Clean build artifacts"

docker-up:
	docker-compose up -d redis

docker-down:
	docker-compose down

seed-redis:
	docker-compose up seed-redis

build:
	@echo "Building CLI..."
	cd cli && pip install -e .
	@echo "Building API..."
	cd api && pip install -r requirements.txt
	@echo "Building Cost Engine..."
	cd cost-engine && go build -o bin/cost-engine .
	@echo "Building Scraper..."
	cd scraper && go build -o bin/scraper .

test:
	@echo "Running Cost Engine tests..."
	cd cost-engine && go test ./...
	@echo "Running API tests..."
	cd api && pytest tests/
	@echo "Running CLI tests..."
	cd cli && pytest tests/

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf cli/venv api/venv
	rm -rf cost-engine/bin scraper/bin

