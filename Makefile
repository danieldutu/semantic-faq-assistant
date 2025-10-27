.PHONY: help setup start stop restart logs seed test clean

help:
	@echo "FAQ Assistant - Available Commands:"
	@echo ""
	@echo "  make setup        - Create virtual environment and install dependencies"
	@echo "  make start        - Start all Docker services"
	@echo "  make stop         - Stop all Docker services"
	@echo "  make restart      - Restart all Docker services"
	@echo "  make logs         - View application logs"
	@echo "  make seed         - Seed database with FAQ data"
	@echo "  make test         - Run test cases"
	@echo "  make clean        - Stop services and remove volumes"
	@echo ""

setup:
	@echo "Creating virtual environment..."
	python3 -m venv faq_venv
	@echo "Activating virtual environment and installing dependencies..."
	. faq_venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "✓ Setup complete! Activate with: source faq_venv/bin/activate"

start:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "✓ Services started! Waiting for health checks..."
	sleep 10
	docker-compose ps

stop:
	@echo "Stopping Docker services..."
	docker-compose down
	@echo "✓ Services stopped"

restart:
	@echo "Restarting Docker services..."
	docker-compose restart
	@echo "✓ Services restarted"

logs:
	@echo "Viewing application logs (Ctrl+C to exit)..."
	docker-compose logs -f app

seed:
	@echo "Seeding database with FAQ data..."
	docker-compose exec app python scripts/seed_database.py --force
	@echo "✓ Database seeded"

test:
	@echo "Running health check..."
	@curl -s http://localhost:8000/health | jq
	@echo ""
	@echo "Testing local match..."
	@curl -s -X POST "http://localhost:8000/ask-question" \
	  -H "Content-Type: application/json" \
	  -H "Authorization: Bearer faq-assistant-secret-key-2024" \
	  -d '{"user_question": "How do I reset my password?"}' | jq
	@echo ""
	@echo "✓ Basic tests complete. For comprehensive testing, run: ./run_tests.sh"
	@echo "Note: Requires 'jq' installed (brew install jq / apt install jq)"

clean:
	@echo "Stopping services and removing volumes..."
	docker-compose down -v
	@echo "✓ Cleanup complete"
