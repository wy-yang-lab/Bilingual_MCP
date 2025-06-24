.PHONY: help install dev test clean docker-build docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install black isort mypy

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=app --cov-report=html

lint: ## Run linting
	black app/ tests/
	isort app/ tests/
	mypy app/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start services
	docker-compose up -d

docker-down: ## Stop services
	docker-compose down

docker-logs: ## View logs
	docker-compose logs -f

run-local: ## Run locally for development
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

demo: ## Test the API with sample request
	curl -H "Authorization: Bearer TEST_TOKEN" \
	     -H "Content-Type: application/json" \
	     -X POST http://localhost:8000/context-request \
	     -d '{"text":"Please login to continue","lang":"en"}' 