#!/bin/bash

# Development Setup Script
# Sets up the development environment without Docker

set -e

echo "========================================="
echo "  AI Travel Agent - Dev Setup           "
echo "========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Check Node.js version
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

echo "Node.js version: $(node --version)"

# Setup backend
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate

echo "Creating superuser (optional)..."
python manage.py createsuperuser --noinput || true

cd ..

# Setup frontend
echo ""
echo "Setting up frontend..."
cd frontend

echo "Installing Node dependencies..."
npm install

cd ..

echo ""
echo "========================================="
echo "  Development setup complete!           "
echo "========================================="
echo ""
echo "To run backend (in backend/ directory):"
echo "  source venv/bin/activate"
echo "  python manage.py runserver 0.0.0.0:8109"
echo ""
echo "To run frontend (in frontend/ directory):"
echo "  npm run dev"
echo ""
echo "To run Celery worker (in backend/ directory):"
echo "  celery -A travel_agent worker -l info"
echo ""
