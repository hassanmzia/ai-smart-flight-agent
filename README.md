# AI Smart Flight Agent

> **A production-grade, multi-agent AI travel planning system** that leverages LangGraph orchestration, real-time search APIs, and conversational AI to deliver end-to-end travel planning — from flight and hotel search to day-by-day itinerary generation, restaurant recommendations, and payment processing.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
  - [System Architecture Diagram](#system-architecture-diagram)
  - [Technology Stack](#technology-stack)
  - [Service Topology](#service-topology)
- [Multi-Agent AI System](#multi-agent-ai-system)
  - [LangGraph Pipeline](#langgraph-pipeline)
  - [Agent Descriptions](#agent-descriptions)
  - [Enhanced Orchestrator](#enhanced-orchestrator)
  - [MCP Server](#mcp-server)
- [Frontend Application](#frontend-application)
  - [Pages and Routes](#pages-and-routes)
  - [State Management](#state-management)
  - [Services Layer](#services-layer)
  - [AI Chat Widget](#ai-chat-widget)
- [Backend API](#backend-api)
  - [Django Applications](#django-applications)
  - [API Endpoints](#api-endpoints)
  - [Authentication](#authentication)
  - [Background Tasks](#background-tasks)
- [Data Layer](#data-layer)
- [External Integrations](#external-integrations)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Running with Docker Compose](#running-with-docker-compose)
  - [Development Mode](#development-mode)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Security](#security)
- [Monitoring and Logging](#monitoring-and-logging)
- [Mobile Support](#mobile-support)
- [Data Flow Diagrams](#data-flow-diagrams)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

AI Smart Flight Agent is a comprehensive travel planning platform that combines **10+ specialized AI agents** with real-world search APIs to deliver intelligent, data-driven travel recommendations. The system uses a **LangGraph state-graph pipeline** to orchestrate multiple agents sequentially — each agent searches, evaluates, and scores travel options using goal-based and utility-based reasoning.

### What Makes It Different

| Feature | Description |
|---------|-------------|
| **Multi-Agent Architecture** | 9 specialized agents (flight, hotel, car, restaurant, goal, utility, evaluators, manager) working in a coordinated pipeline |
| **Real Search Data** | Live flight/hotel/car/restaurant data via SerpAPI (Google Flights, Hotels, Local) |
| **LLM-Powered Itineraries** | GPT-4o-mini generates day-by-day plans with specific times, costs, transit directions |
| **Destination Intelligence** | Weather, safety, visa, packing, local customs, events — all date-and-location-specific |
| **Conversational AI Chat** | Natural-language trip planning with voice input, user context, and memory |
| **Full Booking Pipeline** | Search -> Select -> Book -> Pay (Stripe) -> Confirm -> Itinerary |
| **Real-Time Notifications** | WebSocket-based notifications via Django Channels + Redis |

---

## Key Features

### Travel Search and Booking
- Flight search with city-to-IATA resolution and SerpAPI Google Flights integration
- Hotel search with rating, price, amenity filtering via SerpAPI Google Hotels
- Car rental search via SerpAPI Google Local with multi-city support
- Restaurant discovery with cuisine filtering via SerpAPI Google Local
- Stripe-powered payment processing with secure checkout
- Booking management (create, view, cancel, update)

### AI-Powered Planning
- Natural language trip planning via conversational chat
- 9-agent LangGraph sequential pipeline with shared state
- Goal-based evaluation (budget constraints, penalty/reward scoring)
- Utility-based ranking (price + rating + distance weighted scores)
- LLM-generated day-by-day itineraries with real booking data
- Enhanced destination intelligence (weather, safety, visa, packing, local customs)
- RAG pipeline with ThreadPoolExecutor for parallel agent execution

### User Experience
- 32+ pages with responsive design (mobile-first)
- Dark mode support across all pages
- Real-time WebSocket notifications
- Voice input for AI chat (Web Speech API)
- PDF export for itineraries
- Interactive dashboard with analytics
- Price alerts with background monitoring

---

## Architecture

### System Architecture Diagram

> See `docs/architecture-diagram.drawio` for the full interactive diagram (open with draw.io or diagrams.net).
> See `docs/technical-architecture.pptx` for the PowerPoint presentation.

```
+---------------------------------------------------------------------+
|                        CLIENT LAYER                                  |
|   Browser ---- Mobile App ---- API Client                           |
|                    HTTPS / WSS / REST                                |
+----------------------------+----------------------------------------+
                             |
+----------------------------v----------------------------------------+
|                   NGINX REVERSE PROXY                                |
|   Port 80/443 | SSL Termination | Gzip | WebSocket Upgrade          |
|   / -> :3090  | /api/ -> :8109 | /ws/ -> :8109  | /mcp/ -> :8107   |
+---+----------------+----------------+---------------+---------------+
    |                |                |               |
+---v---+     +------v------+   +----v----+    +-----v----+
|Frontend|    |  Backend    |   | Celery  |    |   MCP    |
|React 18|    |Django 5.0   |   | Worker  |    | Server   |
| :3090  |    |  :8109      |   |+ Beat   |    | :8107    |
|Vite+TS |    |DRF+Channels |   |RabbitMQ |    |FastAPI   |
+--------+    +------+------+   +----+----+    +----+-----+
                     |               |              |
         +-----------+---------------+--------------+
         |           |               |              |
    +----v----+ +----v----+   +------v----+   +-----v--------+
    |PostgreSQL| |  Redis  |   | RabbitMQ |   | External     |
    |  :5438   | |  :6384  |   |  :5673   |   | APIs         |
    |Users,    | |DB0=Cache|   |Celery    |   |OpenAI, Serp  |
    |Bookings  | |DB1=WS+  |   |Broker    |   |Stripe, SMTP  |
    |Payments  | |MCP Queue|   |Task Queue|   |Weather, 11L  |
    +----------+ +---------+   +----------+   +--------------+
```

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | React, TypeScript, Vite | 18.x, 5.x, 5.x |
| **State** | Zustand, React Query | 4.x, 5.x |
| **Styling** | TailwindCSS | 3.x |
| **Backend** | Django, Django REST Framework | 5.0, 3.15 |
| **ASGI** | Daphne, Django Channels | 4.x, 4.x |
| **WSGI** | Gunicorn | 22.x |
| **AI/ML** | LangChain, LangGraph, OpenAI | 0.2.x, 0.2.x |
| **MCP Server** | FastAPI, Uvicorn | 0.110+, 0.27+ |
| **Database** | PostgreSQL | 15 |
| **Cache** | Redis | 7 |
| **Message Broker** | RabbitMQ | 3.12 |
| **Task Queue** | Celery | 5.3+ |
| **Reverse Proxy** | Nginx | 1.25 |
| **Container** | Docker, Docker Compose | 24+, 2.x |
| **Runtime** | Python, Node.js | 3.11, 20 |

### Service Topology

| Service | Internal Port | External Port | Container Name |
|---------|-------------|---------------|----------------|
| Frontend (React/Vite) | 3090 | 3090 | `frontend` |
| Backend (Django/Gunicorn) | 8109 | 8109 | `backend` |
| MCP Server (FastAPI) | 8107 | 8107 | `mcp-server` |
| Celery Worker | -- | -- | `celery-worker` |
| Celery Beat | -- | -- | `celery-beat` |
| PostgreSQL | 5432 | 5438 | `db` |
| Redis | 6379 | 6384 | `redis` |
| RabbitMQ | 5672/15672 | 5673/15673 | `rabbitmq` |
| Nginx | 80 | 80 | `nginx` |

---

## Multi-Agent AI System

### LangGraph Pipeline

The core of the system is a **LangGraph StateGraph** that orchestrates 9 specialized agents in a sequential pipeline. Each agent reads from and writes to a shared `TravelAgentState` dictionary.

```
START
  |
  v
+--------------+    +--------------+    +--------------+    +--------------+
| Flight Agent |===>| Hotel Agent  |===>|Car Rental    |===>|Restaurant    |
|              |    |              |    |Agent         |    |Agent         |
|SerpAPI       |    |SerpAPI       |    |SerpAPI       |    |SerpAPI       |
|Google Flights|    |Google Hotels |    |Google Local  |    |Google Local  |
+--------------+    +--------------+    +--------------+    +--------------+
                                                                   |
  +----------------------------------------------------------------+
  v
+--------------+    +--------------+    +--------------+    +--------------+
| Goal-Based   |===>| Utility-Based|===>| Car Rental   |===>| Restaurant   |
| Evaluator    |    | Evaluator    |    | Evaluator    |    | Evaluator    |
|              |    |              |    |              |    |              |
|Budget check  |    |Hotel ranking |    |Price+Type    |    |Rating+Price  |
|Penalty/Reward|    |Price+Rating  |    |+Rating score |    |+Reviews score|
+--------------+    +--------------+    +--------------+    +--------------+
                                                                   |
                                                                   v
                                                        +------------------+
                                                        |  Manager Agent   |
                                                        |                  |
                                                        |Final compilation |
                                                        |Top 5 rankings   |
                                                        |Total cost calc   |
                                                        +--------+---------+
                                                                 |
                                                                 v
                                                               END
```

### Agent Descriptions

| Agent | Role | Data Source | Key Output |
|-------|------|------------|------------|
| **Flight Agent** | Search flights, resolve city to IATA codes | SerpAPI Google Flights | `flight_results` (top flights with price, duration, stops) |
| **Hotel Agent** | Search hotels near destination | SerpAPI Google Hotels | `hotel_results` (top hotels with price, rating, amenities) |
| **Car Rental Agent** | Find car rentals at destination | SerpAPI Google Local | `car_rental_results` (companies, prices, vehicle types) |
| **Restaurant Agent** | Discover restaurants with cuisine filter | SerpAPI Google Local | `restaurant_results` (restaurants with rating, cuisine, cost) |
| **Goal-Based Evaluator** | Budget evaluation with penalty/reward | Flight + Hotel results | `goal_evaluation` (budget_met, under/over, recommendation) |
| **Utility-Based Evaluator** | Multi-criteria hotel ranking | Hotel results | `utility_evaluation` (weighted score: price, rating, distance) |
| **Car Rental Evaluator** | Score car options | Car rental results | `car_evaluation` (utility scores per option) |
| **Restaurant Evaluator** | Score restaurant options | Restaurant results | `restaurant_evaluation` (utility scores per option) |
| **Manager Agent** | Compile final recommendations | All evaluations | `final_recommendation` (top picks, total cost, rankings) |

### Shared State (TravelAgentState)

```python
{
    "messages": [],              # LangGraph message history
    "user_query": str,           # Original user query
    "origin": str,               # Departure airport/city
    "destination": str,          # Arrival airport/city
    "departure_date": str,       # YYYY-MM-DD
    "return_date": str,          # YYYY-MM-DD
    "passengers": int,           # Number of travelers
    "budget": float,             # Total budget in USD
    "cuisine": str,              # Preferred cuisine type
    "flight_results": dict,      # Flight agent output
    "hotel_results": dict,       # Hotel agent output
    "car_rental_results": dict,  # Car rental agent output
    "restaurant_results": dict,  # Restaurant agent output
    "goal_evaluation": dict,     # Goal evaluator output
    "utility_evaluation": dict,  # Utility evaluator output
    "car_evaluation": dict,      # Car evaluator output
    "restaurant_evaluation": dict, # Restaurant evaluator output
    "final_recommendation": dict # Manager agent output
}
```

### Enhanced Orchestrator

Beyond the core 9-agent pipeline, the **Enhanced Orchestrator** provides additional intelligence:

- **RAG Pipeline** -- Retrieval-Augmented Generation for context-aware responses
- **ThreadPoolExecutor (8 workers)** -- Parallel execution of sub-agents
- **Sub-Agents**:
  - Health and Safety Agent (travel safety scores, CDC health notices)
  - Visa Requirements Agent (visa needs, documents, max stay)
  - Packing Agent (weather-specific packing lists)
  - Local Expert Agent (customs, language, dining etiquette)
- **LLM Destination Intelligence** -- Date-aware, location-specific intelligence covering weather forecasts, transportation, safety, local events, customs, must-see attractions, food scene, and packing essentials
- **Redis Caching** -- TTL-based caching for agent results (flights: 15min, weather: 30min, safety: 24h, visa: 7 days)
- **Narrative Synthesis** -- GPT-4o-mini generates a complete day-by-day itinerary integrating all agent data with specific times, costs, transit directions, and restaurant assignments

### MCP Server

The **Model Context Protocol (MCP) Server** enables agent-to-agent communication:

- **Technology**: FastAPI + Uvicorn on port 8107
- **Agent Registration**: Agents register with `{agent_id, type, capabilities}`
- **Message Types**: Request, Response, Notification, Error
- **Transport**: WebSocket (`/ws/{agent_id}`) + REST endpoints
- **Storage**: Redis DB 1 for agent state, message queues, and shared context
- **Connection Manager**: Maintains active WebSocket pool with broadcast capability
- **Context Sharing**: Session-scoped context with configurable TTL

---

## Frontend Application

### Pages and Routes

The frontend includes **32+ pages** built with React 18, TypeScript, and TailwindCSS:

| Category | Pages |
|----------|-------|
| **Core** | Home, AI Planner, Dashboard, Profile |
| **Search** | Flight Search, Hotel Search, Car Rental Search, Restaurant Search, Tourist Attractions |
| **Results** | Flight Results, Hotel Results |
| **Booking** | Booking, Payment |
| **Itinerary** | Itinerary List, Itinerary Detail |
| **Explore** | Events, Shopping, Attractions |
| **Travel Info** | Weather, Safety, Commute/Traffic |
| **Notifications** | Real-time notification center |
| **Admin** | Admin Dashboard |
| **Auth** | Login, Register |
| **Static** | About, Contact, FAQ, Privacy, Terms |

### State Management

- **Zustand** stores for client state:
  - `authStore` -- User authentication, tokens, session management
  - `bookingStore` -- Current booking, booking list, CRUD operations
  - `notificationStore` -- Real-time notifications, unread count
  - `searchStore` -- Flight/hotel search params and results

- **React Query (TanStack Query)** for server state:
  - Automatic caching, refetching, and invalidation
  - Used for all API data fetching (bookings, itineraries, analytics, etc.)

### Services Layer

20 service modules handle API communication:

| Service | Purpose |
|---------|---------|
| `api.ts` | Axios instance with JWT interceptor, token refresh, error handling |
| `agentService.ts` | AI chat, context management, suggestions |
| `flightService.ts` | Flight search, details, booking |
| `hotelService.ts` | Hotel search, details, booking |
| `bookingService.ts` | Booking CRUD, cancellation |
| `paymentService.ts` | Stripe payment processing |
| `itineraryService.ts` | Itinerary CRUD, day/item management |
| `notificationService.ts` | Notification list, mark as read |
| `authService.ts` | Login, register, token refresh, user profile |
| `carRentalService.ts` | Car rental search |
| `restaurantService.ts` | Restaurant search |
| `weatherService.ts` | Weather data |
| `eventService.ts` | Event search |
| `shoppingService.ts` | Shopping venue search |
| `safetyService.ts` | Safety data |
| `commuteService.ts` | Traffic/commute data |
| `analyticsService.ts` | Dashboard analytics |
| `attractionService.ts` | Tourist attraction search |
| `reviewService.ts` | Review management |
| `priceAlertService.ts` | Price alert CRUD |

### AI Chat Widget

The floating **AI Travel Assistant** chat widget provides:

- **Conversational trip planning** -- Natural language to structured trip parameters
- **User context awareness** -- Knows about user's bookings, itineraries, and preferences
- **Multi-turn conversation** -- Maintains conversation history (last 20 messages)
- **Quick action prompts** -- "Plan a trip", "My bookings", "Recommend a destination", "Travel tips"
- **Voice input** -- Web Speech API integration for hands-free input on mobile
- **Parameter extraction** -- Shows extracted trip parameters as pills (origin, destination, dates, budget)
- **Trip confirmation** -- "Plan My Trip!" button when all required params are collected
- **Mobile-first design** -- Full-screen on mobile, floating panel on desktop
- **Dark mode support** -- Adapts to system/user theme preference

---

## Backend API

### Django Applications

19 Django apps organized under `backend/apps/`:

| App | Models | Description |
|-----|--------|-------------|
| `users` | User, UserProfile | Custom user model with travel preferences, passport info, loyalty programs |
| `agents` | AgentSession, AgentExecution, AgentLog | Multi-agent system orchestration, session tracking, execution logging |
| `flights` | -- | Flight search via SerpAPI, city-to-IATA resolution |
| `hotels` | -- | Hotel search via SerpAPI, rating/amenity filtering |
| `bookings` | Booking | Booking management (flight, hotel, car, restaurant) with status tracking |
| `payments` | Payment | Stripe payment processing, payment records |
| `itineraries` | Itinerary, ItineraryDay, ItineraryItem | Day-by-day itinerary management, AI-generated plans |
| `notifications` | Notification | Real-time and persistent notifications |
| `reviews` | Review | User reviews for hotels, restaurants, attractions |
| `analytics` | -- | Dashboard analytics, booking statistics |
| `car_rentals` | -- | Car rental search via SerpAPI Google Local |
| `restaurants` | -- | Restaurant search with cuisine filtering |
| `attractions` | -- | Tourist attraction search and details |
| `tourist_attractions` | -- | Extended attraction data |
| `weather` | -- | Weather data via OpenWeatherMap API |
| `events` | -- | Local event search |
| `shopping` | -- | Shopping venue search |
| `safety` | -- | Travel safety data, crime levels, health notices |
| `commute` | -- | Traffic and transportation data |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | User login, returns JWT tokens |
| `POST` | `/api/auth/register` | User registration with auto-login |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `GET` | `/api/auth/me` | Get current user profile |
| `POST` | `/api/agents/plan-trip/` | Run full multi-agent trip planning |
| `POST` | `/api/agents/chat` | Conversational AI assistant |
| `POST` | `/api/agents/text-to-speech/` | ElevenLabs TTS |
| `GET` | `/api/flights/search/` | Search flights |
| `GET` | `/api/hotels/search/` | Search hotels |
| `GET/POST` | `/api/bookings/bookings/` | List/create bookings |
| `POST` | `/api/payments/process/` | Process Stripe payment |
| `GET/POST` | `/api/itineraries/itineraries/` | List/create itineraries |
| `GET` | `/api/notifications/` | List notifications |
| `GET` | `/api/analytics/summary/` | Dashboard analytics |
| `GET` | `/api/car-rentals/search/` | Search car rentals |
| `GET` | `/api/restaurants/search/` | Search restaurants |
| `GET` | `/api/weather/` | Get weather data |
| `GET` | `/api/events/` | Get local events |
| `GET` | `/api/safety/` | Get safety data |

### Authentication

- **JWT (SimpleJWT)** with access (1 hour) and refresh (7 day) tokens
- Axios interceptor automatically adds `Bearer` token to all requests
- Automatic token refresh on 401 responses
- Tokens stored in `localStorage` via Zustand `authStore`
- `AllowAny` on search/chat endpoints for unauthenticated access

### Background Tasks

- **Celery Worker** (4 concurrent workers) -- Async task processing
- **Celery Beat** (DB Scheduler) -- Scheduled/periodic tasks
- **Broker**: RabbitMQ via AMQP protocol
- **Result Backend**: `django-celery-results`
- **Beat Scheduler**: `django-celery-beat` (database-backed)
- Tasks: Email notifications, price monitoring, analytics aggregation

---

## Data Layer

### PostgreSQL 15

Primary relational database storing all application data:
- User accounts and profiles
- Bookings (flight, hotel, car, restaurant)
- Payments and transaction history
- Itineraries with day-by-day plans
- Reviews and ratings
- Agent sessions, executions, and logs
- Notification records
- Analytics data
- Connection pooling: `CONN_MAX_AGE=600`

### Redis 7

Multi-purpose in-memory data store:
- **DB 0**: Django cache backend (page cache, query cache, agent result cache)
- **DB 1**: Django Channels layer (WebSocket state) + MCP Server (agent queues, shared context, pub/sub)
- Cache TTLs: Flights 15min, Hotels 15min, Weather 30min, Trip Plans 30min, Health/Safety 24h, Visa 7 days

### RabbitMQ 3.12

Message broker for async task processing:
- AMQP protocol on port 5672 (external: 5673)
- Management UI on port 15672 (external: 15673)
- Celery broker for task distribution
- Management Alpine image for lightweight deployment

---

## External Integrations

| Service | Usage | Required Key |
|---------|-------|-------------|
| **OpenAI** | GPT-4o-mini for NLP, trip planning, itinerary generation | `OPENAI_API_KEY` |
| **SerpAPI** | Google Flights, Hotels, and Local search | `SERP_API_KEY` |
| **Stripe** | Payment processing (charges, refunds) | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` |
| **OpenWeatherMap** | Weather forecasts and current conditions | `WEATHER_API_KEY` |
| **Gmail SMTP** | Email notifications (booking confirmations, etc.) | `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` |
| **ElevenLabs** | Text-to-speech audio generation | `ELEVENLABS_API_KEY` |

---

## Getting Started

### Prerequisites

- Docker 24+ and Docker Compose 2.x
- Git

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-smart-flight-agent
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Edit `.env` with your API keys:
```env
# Required
OPENAI_API_KEY=sk-...
SERP_API_KEY=...

# Optional (for full functionality)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
WEATHER_API_KEY=...
ELEVENLABS_API_KEY=...
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
```

### Running with Docker Compose

```bash
# Build and start all services
docker compose up --build -d

# Check service health
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

Access the application:
- **Frontend**: http://localhost:3090
- **Backend API**: http://localhost:8109/api/
- **API Docs (Swagger)**: http://localhost:8109/api/docs/
- **API Docs (ReDoc)**: http://localhost:8109/api/redoc/
- **RabbitMQ Management**: http://localhost:15673

### Development Mode

For local development without Docker:

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8109
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Celery:**
```bash
cd backend
celery -A travel_agent worker -l info --concurrency=4
celery -A travel_agent beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## API Documentation

Interactive API documentation is available when the backend is running:

- **Swagger UI**: `GET /api/docs/` -- Interactive API explorer
- **ReDoc**: `GET /api/redoc/` -- Beautiful API reference
- **OpenAPI Schema**: `GET /api/schema/` -- Raw JSON schema

Generated by `drf-spectacular`.

---

## Project Structure

```
ai-smart-flight-agent/
|-- frontend/                    # React 18 + TypeScript + Vite
|   |-- src/
|   |   |-- components/          # Reusable UI components
|   |   |   |-- booking/         # AgentChat, booking components
|   |   |   |-- common/          # Button, Card, Loading, Modal
|   |   |   |-- layout/          # Header, Footer
|   |   |   |-- car/             # Car rental components
|   |   |   |-- restaurant/      # Restaurant components
|   |   |   +-- ...
|   |   |-- pages/               # 32+ page components
|   |   |-- services/            # 20 API service modules
|   |   |-- store/               # Zustand stores
|   |   |-- hooks/               # Custom hooks (useAgentChat, useAuth, useNotifications, useWebSocket)
|   |   |-- types/               # TypeScript type definitions
|   |   |-- utils/               # Constants, helpers
|   |   |-- App.tsx              # Router configuration
|   |   +-- main.tsx             # Entry point
|   |-- index.html
|   |-- tailwind.config.js
|   |-- tsconfig.json
|   |-- vite.config.ts
|   +-- package.json
|-- backend/                     # Django 5.0 + DRF
|   |-- apps/
|   |   |-- agents/              # Multi-agent system
|   |   |   |-- agent_tools.py   # LangChain tools (flight, hotel, car, restaurant search)
|   |   |   |-- multi_agent_system.py  # LangGraph StateGraph pipeline
|   |   |   |-- enhanced_orchestrator.py  # Enhanced agents + RAG
|   |   |   |-- enhanced_agents.py  # Health, Visa, Packing, Local Expert agents
|   |   |   |-- views.py         # plan_travel + chat + TTS endpoints
|   |   |   +-- ...
|   |   |-- users/               # Custom user model + profiles
|   |   |-- flights/             # Flight search views
|   |   |-- hotels/              # Hotel search views
|   |   |-- bookings/            # Booking CRUD
|   |   |-- payments/            # Stripe integration
|   |   |-- itineraries/         # Itinerary management
|   |   |-- notifications/       # Notification system
|   |   |-- reviews/             # Review system
|   |   |-- analytics/           # Dashboard analytics
|   |   |-- car_rentals/         # Car rental search
|   |   |-- restaurants/         # Restaurant search
|   |   |-- attractions/         # Attraction search
|   |   |-- weather/             # Weather API integration
|   |   |-- events/              # Event search
|   |   |-- shopping/            # Shopping venue search
|   |   |-- safety/              # Safety data
|   |   |-- commute/             # Traffic data
|   |   +-- tourist_attractions/ # Tourist attraction data
|   |-- travel_agent/
|   |   |-- settings.py          # Django settings
|   |   |-- urls.py              # Root URL configuration
|   |   |-- asgi.py              # ASGI config (Channels)
|   |   +-- celery.py            # Celery configuration
|   |-- manage.py
|   +-- requirements.txt
|-- mcp-server/                  # FastAPI MCP Server
|   +-- server.py                # Agent registration, messaging, WebSocket
|-- nginx/                       # Nginx reverse proxy
|   |-- nginx.conf
|   +-- conf.d/
|       +-- default.conf         # Routing rules
|-- docs/                        # Documentation
|   |-- architecture-diagram.drawio
|   |-- data-flow-diagram.drawio
|   +-- technical-architecture.pptx
|-- docker-compose.yml           # 8 services orchestration
|-- .env.example                 # Environment template
+-- README.md
```

---

## Configuration

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generated |
| `DEBUG` | Debug mode | `True` |
| `DATABASE_URL` | PostgreSQL connection | `postgres://...@db:5432/travel_agent` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `SERP_API_KEY` | SerpAPI key | Required |
| `STRIPE_SECRET_KEY` | Stripe secret key | Optional |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key | Optional |
| `WEATHER_API_KEY` | OpenWeatherMap key | Optional |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS key | Optional |
| `CELERY_BROKER_URL` | RabbitMQ URL | `amqp://guest:guest@rabbitmq:5672//` |

### Agent Configuration

```python
AGENT_CONFIG = {
    'MODEL': 'gpt-4o-mini',         # LLM model
    'TEMPERATURE': 0.7,              # LLM temperature
    'MAX_TOKENS': 4096,              # Max output tokens
    'REQUEST_TIMEOUT': 120,          # API timeout (seconds)
}
```

---

## Security

### Production Security Features

- **SSL/TLS**: Nginx SSL termination with HTTPS redirect
- **HSTS**: HTTP Strict Transport Security (1 year max-age)
- **XSS Protection**: `X-XSS-Protection: 1; mode=block`
- **Frame Protection**: `X-Frame-Options: DENY`
- **Content Security**: `X-Content-Type-Options: nosniff`
- **CSRF Protection**: Django CSRF middleware enabled
- **Secure Cookies**: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`
- **CORS**: Configured allowed origins
- **JWT**: Short-lived access tokens (1h), longer refresh tokens (7d)
- **Rate Limiting**: Configurable per-endpoint via DRF throttling
- **Input Validation**: DRF serializer validation on all endpoints

---

## Monitoring and Logging

- **Application Logging**: Python `logging` with `RotatingFileHandler` (10MB x 10 backups)
- **Log Levels**: Console (INFO) + File (DEBUG)
- **Docker Health Checks**: All services have health check endpoints
- **Container Restart**: `restart: unless-stopped` on all containers
- **Agent Logging**: `AgentLog` model tracks every agent execution with timing, tokens, and cost

---

## Mobile Support

The application is fully responsive and mobile-optimized:

- **Viewport**: Proper meta viewport tag with `width=device-width, initial-scale=1.0`
- **Touch Targets**: 44px minimum touch targets on mobile
- **Font Size**: 16px minimum on mobile inputs to prevent iOS zoom
- **Mobile Navigation**: Hamburger menu with full navigation drawer
- **AI Chat**: Full-screen on mobile, floating panel on desktop
- **Voice Input**: Web Speech API integration for hands-free AI chat on mobile
- **Safe Areas**: Support for notched devices (`env(safe-area-inset-bottom)`)
- **Responsive Grid**: All pages use TailwindCSS responsive breakpoints (`sm:`, `md:`, `lg:`, `xl:`)

---

## Data Flow Diagrams

> See `docs/data-flow-diagram.drawio` for the full interactive data flow diagram.

### Key Data Flows

1. **Authentication**: User -> Login Form -> POST /api/auth/login -> JWT Generation -> Zustand authStore -> localStorage
2. **Flight Search**: Search Form -> flightService -> GET /api/flights/search -> FlightSearchTool -> SerpAPI Google Flights -> Results
3. **AI Trip Planning**: AI Planner -> POST /api/agents/plan-trip -> LangGraph Pipeline (9 agents) -> Enhanced Orchestrator -> LLM Narrative -> Final Recommendation
4. **Payment Processing**: PaymentPage -> paymentService -> POST /api/payments -> Stripe API -> PostgreSQL -> Celery Email Notification
5. **Real-Time Notifications**: System Event -> Celery Worker -> RabbitMQ -> Django Channels -> Redis Channel Layer -> WebSocket -> Toast UI
6. **MCP Agent Communication**: Agent A -> POST /agents/register -> MCP Server -> Redis Queue -> WebSocket -> Agent B
7. **Itinerary Generation**: ItineraryPage -> Enhanced Orchestrator (RAG + ThreadPool) -> OpenAI GPT-4 -> PostgreSQL -> PDF Export
8. **Caching Strategy**: API Request -> Redis Check -> HIT (return cached) / MISS (query DB/API, store with TTL)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is proprietary. All rights reserved.
