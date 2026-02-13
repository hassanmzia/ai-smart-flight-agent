#!/bin/bash

# AI Travel Agent - Startup Script
# This script starts all services using Docker Compose

set -e

echo "========================================="
echo "  AI Travel Agent - Multi-Agent System  "
echo "========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  WARNING: Please update .env file with your API keys before continuing!"
    echo "   Required keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - SERP_API_KEY"
    echo "   - STRIPE_SECRET_KEY (optional)"
    echo ""
    read -p "Press Enter to continue after updating .env file..."
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p backend/logs
mkdir -p backend/staticfiles
mkdir -p backend/media
mkdir -p frontend/node_modules

echo ""
echo "Building Docker images..."
docker compose build

echo ""
echo "Starting services..."
docker compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# Check PostgreSQL
if docker compose exec -T postgres pg_isready -U travel_admin > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
else
    echo "✗ PostgreSQL is not ready"
fi

# Check Redis
if docker compose exec -T redis redis-cli -p 6384 -a redis_secure_pass_2026 ping > /dev/null 2>&1; then
    echo "✓ Redis is ready"
else
    echo "✗ Redis is not ready"
fi

# Check Nginx (main entry point on port 3090)
if curl -sf http://localhost:3090/api/health > /dev/null 2>&1; then
    echo "✓ Nginx + Backend API is ready"
else
    echo "⚠  Nginx + Backend API is starting..."
fi

# Check Frontend (via nginx)
if curl -sf http://localhost:3090 > /dev/null 2>&1; then
    echo "✓ Frontend is ready (via nginx)"
else
    echo "⚠  Frontend is starting..."
fi

echo ""
echo "========================================="
echo "  Services are starting up!             "
echo "========================================="
echo ""
echo "Access points (all via nginx with SSL on port 3090):"
echo "  🌐 Main Application:    https://demo.eminencetechsolutions.com:3090"
echo "  🔧 Backend API:         https://demo.eminencetechsolutions.com:3090/api"
echo "  📚 API Documentation:   https://demo.eminencetechsolutions.com:3090/api/docs"
echo "  👤 Django Admin:        https://demo.eminencetechsolutions.com:3090/admin"
echo "  🤖 MCP Server:          https://demo.eminencetechsolutions.com:3090/mcp"
echo "  📊 RabbitMQ Management: http://demo.eminencetechsolutions.com:15673"
echo ""
echo "Credentials:"
echo "  RabbitMQ: travel_mq / mq_secure_pass_2026"
echo ""
echo "To view logs: docker compose logs -f [service-name]"
echo "To stop:      ./stop.sh"
echo ""
echo "Note: It may take a few minutes for all services to be fully ready."
echo "========================================="
