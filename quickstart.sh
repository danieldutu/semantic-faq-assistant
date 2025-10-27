#!/bin/bash

# FAQ Assistant - Quick Start Script
# This script sets up and starts the FAQ Assistant system

set -e  # Exit on error

echo "======================================="
echo "FAQ Assistant - Quick Start"
echo "======================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo -e "${BLUE}[1/6] Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Docker is not running. Please start Docker Desktop and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check .env file
echo -e "${BLUE}[2/6] Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env file with your OpenAI API key${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Environment file exists${NC}"
echo ""

# Start Docker services
echo -e "${BLUE}[3/6] Starting Docker services...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for services to be healthy
echo -e "${BLUE}[4/6] Waiting for services to be ready...${NC}"
sleep 15
docker-compose ps
echo ""

# Seed database
echo -e "${BLUE}[5/6] Seeding database with FAQ data...${NC}"
docker-compose exec -T app python scripts/seed_database.py << EOF
no
EOF
echo -e "${GREEN}✓ Database seeded${NC}"
echo ""

# Test the API
echo -e "${BLUE}[6/6] Testing API...${NC}"
HEALTH_CHECK=$(curl -s http://localhost:8000/health)
echo "Health check: $HEALTH_CHECK"
echo ""

# Final instructions
echo -e "${GREEN}======================================="
echo "✓ Setup Complete!"
echo "=======================================${NC}"
echo ""
echo "API is running at: http://localhost:8000"
echo "Documentation: http://localhost:8000/docs"
echo ""
echo "Try a test query:"
echo ""
echo 'curl -X POST "http://localhost:8000/ask-question" \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Bearer faq-assistant-secret-key-2024" \'
echo '  -d '"'"'{"user_question": "How do I reset my password?"}'"'"
echo ""
echo "View logs: docker-compose logs -f app"
echo "Stop services: docker-compose down"
echo ""
