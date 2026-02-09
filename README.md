# 🤖 AI Smart Flight Agent - Multi-Agent Travel Planning System

A comprehensive, professional-grade AI Travel Agent application built with multi-agent AI architecture, featuring goal-based and utility-based agents for intelligent travel planning.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Multi-Agent System](#multi-agent-system)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)

## 🌟 Overview

This application implements a sophisticated multi-agent AI system for travel planning, based on the concepts from the `Goal_Based_&_Utility_Based_Agent.ipynb` notebook. It uses advanced AI agents to help users plan trips, find flights, book hotels, and create comprehensive itineraries.

### Key Highlights

- **Multi-Agent AI Architecture** using LangGraph
- **Goal-Based Agent** for budget-conscious flight recommendations
- **Utility-Based Agent** for hotel evaluation based on price and quality
- **MCP (Model Context Protocol)** for agent-to-agent communication
- **Real-time Updates** via WebSocket
- **Comprehensive Booking System** with payment integration
- **Professional UI** with React, TypeScript, and TailwindCSS

## ✨ Features

### Core Features (from Notebook)

1. **Flight Agent** - Search flights using SerpAPI Google Flights
2. **Hotel Agent** - Hotel search using SerpAPI Google Hotels
3. **Goal-Based Agent** - Budget-based flight evaluation with penalty/reward scoring
4. **Utility-Based Agent** - Multi-criteria hotel evaluation (price + star rating)
5. **Manager Agent** - Orchestrates all agents and compiles recommendations

### Enhanced Professional Features

- User Management & JWT Authentication
- Booking System with multi-item support
- Stripe Payment Integration
- Trip Itinerary Builder with weather and PDF export
- Price Alerts with email notifications
- Restaurant, Attractions, and Car Rental integration
- Analytics Dashboard
- Real-Time WebSocket notifications
- Reviews & Ratings system

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                     │
│                  Port 80 (172.168.1.95)                      │
└─────────────────────────────────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌───────────┐    ┌────────────────┐    ┌────────────────┐
│ Frontend  │    │    Backend     │    │   MCP Server   │
│ React+TS  │    │    Django      │    │    FastAPI     │
│ Port 3090 │    │   Port 8001    │    │   Port 8107    │
└───────────┘    └────────────────┘    └────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌───────────┐    ┌──────────────┐    ┌───────────────┐
│PostgreSQL │    │    Redis     │    │   RabbitMQ    │
│Port 5438  │    │  Port 6384   │    │   Port 5673   │
└───────────┘    └──────────────┘    └───────────────┘
```

## 🛠️ Technology Stack

### Backend
- Django 5.0 + DRF
- PostgreSQL 15
- Redis 7
- Celery + RabbitMQ
- LangChain + LangGraph
- Django Channels (WebSocket)

### Frontend
- React 18 + TypeScript
- Vite
- TailwindCSS
- Zustand + React Query
- Axios

### Infrastructure
- Docker + Docker Compose
- Nginx
- Non-default ports (3090, 8001, 8107, 5438, 6384, 5673)

## 🚀 Getting Started

### Prerequisites

- Docker Desktop or Docker Engine + Docker Compose
- 4GB+ RAM
- API Keys: OpenAI, SerpAPI, Stripe (optional)

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd ai-smart-flight-agent

# 2. Set up environment
cp .env.example .env
# Edit .env and add your API keys

# 3. Start application
chmod +x start.sh stop.sh
./start.sh

# 4. Access application
# Main App: http://172.168.1.95:3090
# API Docs: http://172.168.1.95:8001/api/docs
# Admin:    http://172.168.1.95:8001/admin
```

### Using Make

```bash
make help          # Show all commands
make up            # Start services
make down          # Stop services
make logs          # View logs
make migrate       # Run migrations
```

## 📚 API Documentation

Interactive API documentation available at:
- Swagger UI: http://172.168.1.95:8001/api/docs
- ReDoc: http://172.168.1.95:8001/api/redoc

### Key Endpoints

- `POST /api/auth/token/` - Login
- `GET /api/flights/search/` - Search flights
- `GET /api/hotels/search/` - Search hotels
- `POST /api/agents/execute/` - Execute AI agent task
- `GET /api/bookings/` - List bookings

## 🤖 Multi-Agent System

### Agent Workflow

1. **Manager Agent** receives user query
2. **Flight Agent** searches flights via SerpAPI
3. **Hotel Agent** searches hotels via SerpAPI
4. **Goal-Based Agent** evaluates flights against budget
5. **Utility-Based Agent** ranks hotels by utility score
6. **Manager Agent** compiles final recommendations

### Usage Example

```python
from apps.agents.multi_agent_system import get_travel_system

travel_system = get_travel_system()
result = travel_system.run(
    user_query="Find flights from Paris to Berlin",
    origin="CDG",
    destination="BER",
    departure_date="2025-10-10",
    budget=200.0
)
```

## ⚙️ Configuration

Key environment variables:

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False

# Database
DATABASE_URL=postgresql://user:pass@host:5438/db

# API Keys
OPENAI_API_KEY=sk-...
SERP_API_KEY=...
STRIPE_SECRET_KEY=sk_test_...

# Frontend
REACT_APP_API_URL=http://172.168.1.95:8001
```

## 💻 Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # Starts on port 3090
```

## 🐳 Docker Commands

```bash
# Start
docker compose up -d

# View logs
docker compose logs -f backend

# Execute commands
docker compose exec backend python manage.py migrate

# Stop
docker compose down
```

## 📊 Service Health

- Backend: http://172.168.1.95:8001/api/health
- MCP Server: http://172.168.1.95:8107/health
- RabbitMQ: http://172.168.1.95:15673

## 🚢 Deployment

Production checklist:
- Set `DEBUG=False`
- Configure SSL certificates
- Use production database
- Set up monitoring
- Configure log rotation
- Update API keys

## 📄 License

MIT License

---

**Made with ❤️ using Multi-Agent AI Architecture**
