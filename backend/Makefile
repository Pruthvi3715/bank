# GraphSentinel Makefile

.PHONY: help install test lint run demo docker-build docker-up docker-down clean

help:
	@echo "GraphSentinel - AI-Powered Fund Flow Fraud Detection"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make test          - Run test suite"
	@echo "  make lint          - Run code quality checks"
	@echo "  make run           - Run the API locally"
	@echo "  make run-demo      - Run in demo mode (cached)"
	@echo "  make run-live      - Run with live detection"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start services with docker-compose"
	@echo "  make docker-down   - Stop services"
	@echo "  make clean         - Clean up cache and temp files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

lint:
	ruff check app/ --fix

run:
	uvicorn app.main:app --reload

run-demo:
	DEMO_MODE=1 uvicorn app.main:app --reload

run-live:
	DEMO_MODE=0 uvicorn app.main:app --reload

docker-build:
	cd .. && docker-compose build

docker-up:
	cd .. && docker-compose up -d

docker-down:
	cd .. && docker-compose down

docker-logs:
	cd .. && docker-compose logs -f graphsentinel

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true