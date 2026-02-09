#!/bin/bash

# AI Travel Agent - Stop Script

set -e

echo "Stopping AI Travel Agent services..."
docker compose down

echo ""
echo "Services stopped successfully!"
echo ""
echo "To remove all data (including database):"
echo "  docker compose down -v"
