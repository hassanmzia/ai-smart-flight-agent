# 🤖 AI Smart Flight Agent - Comprehensive Documentation

<div align="center">

![AI Travel Agent](https://img.shields.io/badge/AI-Travel%20Agent-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![Django](https://img.shields.io/badge/Django-5.0-darkgreen)
![React](https://img.shields.io/badge/React-18-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Intelligent Multi-Agent Travel Planning System**

*Built with Goal-Based & Utility-Based AI Agents using LangGraph*

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Testing](#-testing)

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
  - [System Overview](#system-overview)
  - [Multi-Agent System](#multi-agent-system)
  - [Technology Stack](#technology-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#-usage)
  - [Basic Workflow](#basic-workflow)
  - [API Usage](#api-usage)
  - [Agent Execution](#agent-execution)
- [Development](#-development)
  - [Project Structure](#project-structure)
  - [Local Development](#local-development)
  - [Testing](#testing)
- [API Documentation](#-api-documentation)
  - [Endpoints](#key-endpoints)
  - [Authentication](#authentication)
  - [Examples](#api-examples)
- [Deployment](#-deployment)
  - [Docker Deployment](#docker-deployment)
  - [Production Setup](#production-setup)
- [Configuration Reference](#-configuration-reference)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

AI Smart Flight Agent is a professional-grade, production-ready travel planning application that leverages **multi-agent AI architecture** to provide intelligent travel recommendations. The system combines **goal-based reasoning** (budget optimization) and **utility-based evaluation** (multi-criteria scoring) to deliver personalized flight and hotel suggestions.

### Why This Project?

Traditional travel booking platforms simply display search results. This application goes further by:

1. **Understanding User Goals** - Budget constraints, preferences, priorities
2. **Intelligent Evaluation** - Multi-criteria scoring (price, quality, reviews)
3. **Contextual Recommendations** - Not just search, but smart suggestions
4. **Transparent Reasoning** - Explainable AI decisions with scoring details

### Key Innovations

- ✨ **Hybrid Agent Architecture** - Combines goal-based and utility-based reasoning
- 🔄 **LangGraph Orchestration** - State machine for complex agent workflows
- 🎯 **Budget-Aware Recommendations** - Penalty/reward scoring system
- 📊 **Multi-Criteria Optimization** - Price vs. quality trade-offs
- 💳 **End-to-End Booking** - Search, evaluate, book, pay - all in one platform

---

## ✨ Features

### 🤖 AI & Agent Features

<details>
<summary><b>Multi-Agent System (Click to expand)</b></summary>

#### Manager Agent
- **Role**: Orchestrates all agents and compiles final recommendations
- **Capabilities**: Workflow management, state coordination, result aggregation
- **Technology**: LangGraph state machine

#### Flight Agent
- **Role**: Search and retrieve flight options
- **Data Source**: SerpAPI Google Flights API
- **Features**:
  - Multi-city and round-trip support
  - Real-time pricing and availability
  - Airline logos and branding
  - Departure/arrival times
  - Layover and duration information
  - Direct vs. connecting flights

#### Hotel Agent
- **Role**: Search and retrieve hotel options
- **Data Source**: SerpAPI Google Hotels API
- **Features**:
  - Location-based search (city, airport, landmark)
  - Check-in/check-out date filtering
  - Guest capacity filtering
  - Price per night extraction
  - High-quality image galleries
  - Amenities list (WiFi, pool, gym, etc.)
  - Star ratings and guest reviews
  - Booking links to third-party sites

#### Goal-Based Agent
- **Role**: Evaluate flights against user budget
- **Algorithm**:
  ```python
  if flight_price <= user_budget:
      score = 20 + (budget - flight_price) * bonus_multiplier
      status = "within budget"
  else:
      score = -20 - (flight_price - budget) * penalty_multiplier
      status = "over budget"
  ```
- **Output**: Ranked flights with budget status and savings/overage

#### Utility-Based Agent
- **Role**: Multi-criteria hotel evaluation
- **Algorithm**:
  ```python
  # Price Utility (-40 to +40)
  if price < 120: price_score = 40
  elif price < 150: price_score = 20
  elif price < 180: price_score = 0
  elif price < 250: price_score = -20
  else: price_score = -40

  # Rating Utility (-40 to +40)
  if stars == 5: rating_score = 40
  elif stars == 4: rating_score = 20
  elif stars == 3: rating_score = 0
  elif stars == 2: rating_score = -20
  else: rating_score = -40

  # Combined Utility Score
  utility_score = price_score + rating_score  # Range: -80 to +80
  ```
- **Output**: Ranked hotels with utility scores and recommendations

#### Weather Agent
- **Role**: Provide destination weather forecasts
- **Data Source**: Weather API
- **Features**: 7-day forecast, temperature, conditions, precipitation

</details>

### 🎫 Booking & Payment Features

- **Flight Booking**: Multi-passenger, seat selection, baggage options
- **Hotel Booking**: Multi-room, special requests, cancellation policies
- **Payment Processing**: Stripe integration with test/live modes
- **Payment Methods**: Store and manage multiple cards
- **Refunds**: Automated refund processing
- **Booking History**: View past and upcoming trips
- **Booking Confirmation**: Email notifications with details

### 👤 User Management

- **Authentication**: JWT token-based auth with refresh tokens
- **User Profiles**: Personal info, preferences, travel history
- **Password Reset**: Email-based password recovery
- **Social Login**: Google, Facebook (optional)
- **Role-Based Access**: User, Staff, Admin roles
- **Profile Analytics**: Track bookings, spending, favorite destinations

### 📅 Trip Planning

- **Itinerary Builder**: Drag-and-drop trip planning
- **Multi-City Trips**: Complex itineraries with multiple stops
- **Weather Integration**: Forecast for each destination
- **PDF Export**: Printable trip itineraries
- **Calendar Sync**: Export to Google Calendar, iCal
- **Collaborative Planning**: Share itineraries with travel companions

### 🔔 Notifications & Alerts

- **Price Alerts**: Email notifications for price drops
- **Booking Reminders**: Check-in reminders
- **Flight Updates**: Delay/cancellation alerts (future)
- **Promotional Offers**: Personalized deals
- **WebSocket Real-time**: Live updates without page refresh

### 📊 Analytics & Reporting

- **User Dashboard**: Booking statistics, spending trends
- **Admin Analytics**: Platform usage, revenue, popular destinations
- **Agent Performance**: Track AI agent success rates
- **Search Analytics**: Popular routes, peak booking times

### 🌐 Additional Features

- **Reviews & Ratings**: User-generated content
- **Car Rentals**: Integration with car rental APIs
- **Restaurants**: Destination restaurant recommendations
- **Attractions**: Tourist attractions and activities
- **Multi-Currency**: Support for different currencies (future)
- **Multi-Language**: Internationalization support (future)

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Users (Web/Mobile Browsers)                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTPS/WSS
                   ┌─────────────▼────────────┐
                   │   Nginx Reverse Proxy    │
                   │   Port 80 (Public)       │
                   │   - Load Balancing       │
                   │   - SSL Termination      │
                   │   - Static File Serving  │
                   └─────────────┬────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐
  │   Frontend       │  │    Backend      │  │   MCP Server     │
  │   React 18       │  │    Django 5.0   │  │   FastAPI        │
  │   TypeScript     │  │    DRF          │  │   Agent Comms    │
  │   Nginx: 3090    │  │    Nginx: 3090  │  │   Nginx: 3090/mcp│
  └──────────────────┘  └────────┬────────┘  └──────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐
  │   PostgreSQL 15  │  │    Redis 7      │  │   RabbitMQ       │
  │   Main Database  │  │    Cache        │  │   Message Queue  │
  │   Port: 5438     │  │    Sessions     │  │   Port: 5673     │
  └──────────────────┘  └─────────────────┘  └──────────────────┘
                                 │
                   ┌─────────────▼────────────┐
                   │   Celery Workers         │
                   │   - Email Sending        │
                   │   - PDF Generation       │
                   │   - Price Alerts         │
                   └──────────────────────────┘
```

### Multi-Agent System

```
┌──────────────────────────────────────────────────────────────────┐
│                      Manager Agent (LangGraph)                   │
│                    State Machine Orchestration                   │
└────────┬────────┬────────┬────────┬────────┬───────────────────┘
         │        │        │        │        │
         ▼        ▼        ▼        ▼        ▼
    ┌────────┬────────┬────────┬────────┬────────┐
    │ Flight │ Hotel  │Weather │  Goal  │Utility │
    │ Agent  │ Agent  │ Agent  │ Agent  │ Agent  │
    └───┬────┴───┬────┴───┬────┴───┬────┴───┬────┘
        │        │        │        │        │
        ▼        ▼        ▼        ▼        ▼
    ┌────────────────────────────────────────────┐
    │         External APIs                      │
    │  SerpAPI | Weather API | OpenAI | Stripe  │
    └────────────────────────────────────────────┘
```

**Agent Workflow**:
1. User submits travel query (origin, destination, dates, budget)
2. Manager Agent receives query and initializes state
3. Flight Agent searches flights via SerpAPI (parallel)
4. Hotel Agent searches hotels via SerpAPI (parallel)
5. Weather Agent fetches forecast (parallel)
6. Goal-Based Agent evaluates flights against budget
7. Utility-Based Agent ranks hotels by combined score
8. Manager Agent compiles final recommendations
9. Results returned to user via API

### Technology Stack

<details>
<summary><b>Frontend Technologies</b></summary>

| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18.x | UI framework with hooks |
| **TypeScript** | 5.x | Static typing, code quality |
| **Vite** | 5.x | Fast build tool, HMR |
| **TailwindCSS** | 3.x | Utility-first CSS |
| **Zustand** | 4.x | Lightweight state management |
| **React Query** | 5.x | Server state management, caching |
| **Axios** | 1.x | HTTP client |
| **React Router** | 6.x | Client-side routing |
| **shadcn/ui** | Latest | Reusable UI components |
| **Lucide Icons** | Latest | Icon library |

</details>

<details>
<summary><b>Backend Technologies</b></summary>

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Django** | 5.0 | Web framework |
| **Django REST Framework** | 3.15 | RESTful API |
| **PostgreSQL** | 15 | Relational database |
| **Redis** | 7 | Cache, sessions, Celery broker |
| **Celery** | 5.x | Async task processing |
| **RabbitMQ** | 3.13 | Message broker |
| **Django Channels** | 4.x | WebSocket support |
| **LangChain** | 0.1.x | LLM framework |
| **LangGraph** | 0.0.x | Agent state machine |
| **OpenAI Python SDK** | 1.x | GPT-4 integration |
| **Stripe Python SDK** | Latest | Payment processing |
| **SerpAPI** | Latest | Search data |
| **Pillow** | Latest | Image processing |
| **ReportLab** | Latest | PDF generation |

</details>

<details>
<summary><b>Infrastructure & DevOps</b></summary>

| Technology | Purpose |
|-----------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Nginx** | Reverse proxy, load balancer |
| **GitHub Actions** | CI/CD (optional) |
| **PostgreSQL Backups** | Automated backups |
| **Let's Encrypt** | Free SSL certificates (production) |

</details>

---

## 🚀 Getting Started

### Prerequisites

**Required**:
- Docker Desktop 20+ OR Docker Engine + Docker Compose
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)

**For Local Development (without Docker)**:
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

**API Keys** (Required for full functionality):
- OpenAI API key (for GPT-4)
- SerpAPI key (for flight/hotel search)
- Stripe keys (test mode for development)
- Weather API key (optional)

### Installation

#### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-smart-flight-agent.git
cd ai-smart-flight-agent

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env and add your API keys
nano .env  # or use your preferred editor

# Required keys to add:
# OPENAI_API_KEY=sk-...
# SERP_API_KEY=...
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_PUBLISHABLE_KEY=pk_test_...

# 4. Start all services
docker-compose up -d

# 5. Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 6. Run database migrations
docker-compose exec backend python manage.py migrate

# 7. Create superuser (admin account)
docker-compose exec backend python manage.py createsuperuser

# 8. Access the application (all through nginx on port 3090)
# Frontend: https://demo.eminencetechsolutions.com:3090
# API:      https://demo.eminencetechsolutions.com:3090/api/
# Admin:    https://demo.eminencetechsolutions.com:3090/admin/
# API Docs: https://demo.eminencetechsolutions.com:3090/api/docs/
```

#### Option 2: Using Make Commands

```bash
# View all available commands
make help

# Start services
make up

# View logs
make logs

# Run migrations
make migrate

# Create superuser
make superuser

# Stop services
make down

# Restart services
make restart

# Clean everything (including volumes)
make clean
```

#### Option 3: Manual Setup (Local Development)

<details>
<summary><b>Backend Setup</b></summary>

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb travel_agent_db
export DATABASE_URL="postgresql://localhost/travel_agent_db"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver 0.0.0.0:8109
```

</details>

<details>
<summary><b>Frontend Setup</b></summary>

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env and set API URL
echo "VITE_API_URL=http://localhost:3090" >> .env

# Start development server
npm run dev  # Starts on port 3090
```

</details>

### Configuration

#### Environment Variables

**Backend** (`.env`):

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=demo.eminencetechsolutions.com,localhost,backend

# Database
DATABASE_URL=postgresql://travel_admin:password@postgres:5432/travel_agent_db

# Redis
REDIS_URL=redis://:password@redis:6384/0

# RabbitMQ
CELERY_BROKER_URL=amqp://user:password@rabbitmq:5673/

# CORS
CORS_ALLOWED_ORIGINS=https://demo.eminencetechsolutions.com:3090,http://localhost:3090
# Note: All traffic now goes through nginx on port 3090

# API Keys
OPENAI_API_KEY=sk-...
SERP_API_KEY=...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
WEATHER_API_KEY=...

# Email (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=3600
```

**Frontend** (`.env`):

```bash
VITE_API_URL=https://demo.eminencetechsolutions.com:3090
VITE_WS_URL=wss://demo.eminencetechsolutions.com:3090/ws
VITE_MCP_URL=https://demo.eminencetechsolutions.com:3090/mcp
PORT=3090
```

---

## 💻 Usage

### Basic Workflow

1. **Search Flights**:
   ```
   Navigate to: https://demo.eminencetechsolutions.com:3090/flights
   Enter: Origin (e.g., LAX), Destination (e.g., JFK)
   Dates: Departure and return dates
   Click: Search Flights
   ```

2. **Search Hotels**:
   ```
   Navigate to: https://demo.eminencetechsolutions.com:3090/hotels
   Enter: Location, Check-in, Check-out dates
   Click: Search Hotels
   ```

3. **AI-Powered Planning**:
   ```
   Navigate to: https://demo.eminencetechsolutions.com:3090/ai-planner
   Enter: Origin, Destination, Dates, Budget
   Click: Plan My Trip
   AI agents will:
   - Search flights and hotels
   - Evaluate against budget
   - Rank by utility scores
   - Return best recommendations
   ```

4. **Book & Pay**:
   ```
   Select recommended flight/hotel
   Click: Book Now
   Fill traveler details
   Enter payment info (use test card: 4242 4242 4242 4242)
   Complete booking
   ```

### API Usage

#### Authentication

```bash
# Register
curl -X POST https://demo.eminencetechsolutions.com:3090/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Login
curl -X POST https://demo.eminencetechsolutions.com:3090/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Flight Search

```bash
curl -X GET "https://demo.eminencetechsolutions.com:3090/api/flights/search/?origin=LAX&destination=JFK&departure_date=2026-06-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Hotel Search

```bash
curl -X GET "https://demo.eminencetechsolutions.com:3090/api/hotels/search/?location=New%20York&check_in=2026-06-01&check_out=2026-06-05" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### AI Agent Execution

```bash
curl -X POST https://demo.eminencetechsolutions.com:3090/api/agents/execute/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a trip from Paris to Berlin",
    "origin": "CDG",
    "destination": "TXL",
    "departure_date": "2026-07-15",
    "return_date": "2026-07-20",
    "budget": 500.0
  }'
```

### Agent Execution

**Python SDK**:

```python
from apps.agents.multi_agent_system import get_travel_system

# Initialize system
travel_system = get_travel_system()

# Execute agents
result = travel_system.run(
    user_query="Find budget-friendly flights from NYC to LA",
    origin="JFK",
    destination="LAX",
    departure_date="2026-08-10",
    return_date="2026-08-17",
    budget=400.0,
    adults=2
)

# Access results
print(f"Recommended Flight: {result['recommended_flight']}")
print(f"Recommended Hotel: {result['recommended_hotel']}")
print(f"Budget Analysis: {result['budget_analysis']}")
print(f"Utility Scores: {result['hotel_rankings']}")
```

---

## 👨‍💻 Development

### Project Structure

```
ai-smart-flight-agent/
├── backend/                    # Django backend
│   ├── apps/                   # Django applications
│   │   ├── agents/            # AI agents & LangGraph
│   │   │   ├── agent_tools.py        # Agent implementations
│   │   │   ├── multi_agent_system.py # LangGraph orchestration
│   │   │   ├── integrations/         # External API clients
│   │   │   │   └── stripe_client.py
│   │   │   └── tasks.py              # Celery tasks
│   │   ├── users/             # User management
│   │   ├── flights/           # Flight search & booking
│   │   ├── hotels/            # Hotel search & booking
│   │   ├── bookings/          # Booking management
│   │   ├── payments/          # Payment processing
│   │   ├── itineraries/       # Trip planning
│   │   ├── reviews/           # Reviews & ratings
│   │   ├── notifications/     # Alerts & emails
│   │   ├── analytics/         # Usage tracking
│   │   ├── car_rentals/       # Car rental integration
│   │   ├── restaurants/       # Restaurant recommendations
│   │   └── attractions/       # Tourist attractions
│   ├── travel_agent/          # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   ├── utils/                 # Shared utilities
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # Reusable components
│   │   │   ├── flight/       # Flight components
│   │   │   ├── hotel/        # Hotel components
│   │   │   ├── layout/       # Layout components
│   │   │   └── ui/           # shadcn/ui components
│   │   ├── pages/            # Page components
│   │   │   ├── HomePage.tsx
│   │   │   ├── FlightSearchPage.tsx
│   │   │   ├── HotelSearchPage.tsx
│   │   │   ├── AIPlannerPage.tsx
│   │   │   ├── BookingPage.tsx
│   │   │   ├── PaymentPage.tsx
│   │   │   └── DashboardPage.tsx
│   │   ├── services/         # API services
│   │   │   ├── flightService.ts
│   │   │   ├── hotelService.ts
│   │   │   ├── bookingService.ts
│   │   │   └── paymentService.ts
│   │   ├── store/            # Zustand stores
│   │   ├── types/            # TypeScript types
│   │   ├── utils/            # Utilities
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── mcp-server/               # Model Context Protocol server
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/                    # Nginx configuration
│   ├── nginx.conf
│   └── Dockerfile
├── docs/                     # Documentation
│   ├── architecture-diagram.drawio
│   ├── ARCHITECTURE_PRESENTATION.md
│   └── API.md
├── docker-compose.yml        # Docker orchestration
├── .env.example              # Environment template
├── Makefile                  # Make commands
├── README.md                 # This file
├── TESTING_BOOKINGS.md       # Testing guide
└── TEST_CARDS_QUICK_REF.md   # Test card reference
```

### Local Development

#### Backend Development

```bash
# Activate virtual environment
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
python backend/manage.py migrate

# Create superuser
python backend/manage.py createsuperuser

# Run development server
python backend/manage.py runserver 0.0.0.0:8109

# Run Celery worker (separate terminal)
celery -A travel_agent worker --loglevel=info

# Run Celery beat (separate terminal)
celery -A travel_agent beat --loglevel=info

# Run Django shell
python backend/manage.py shell

# Create migrations
python backend/manage.py makemigrations

# Run tests
pytest backend/
```

#### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Start development server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code
npm run format

# Run tests
npm test
```

### Testing

**Backend Tests**:

```bash
# Run all tests
pytest

# Run specific app tests
pytest apps/agents/tests/

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test
pytest apps/agents/tests/test_agent_tools.py::test_flight_search
```

**Frontend Tests**:

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

**Integration Tests**:

```bash
# Test API endpoints
python backend/manage.py test apps.agents.tests.test_api

# Test agent workflows
python backend/manage.py test apps.agents.tests.test_workflows
```

**Payment Testing** (See `TESTING_BOOKINGS.md`):

- Use Stripe test cards (e.g., `4242 4242 4242 4242`)
- No real money charged
- Full payment flow testing

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: https://demo.eminencetechsolutions.com:3090/api/docs/
- **ReDoc**: https://demo.eminencetechsolutions.com:3090/api/redoc/

### Key Endpoints

#### Authentication

```
POST   /api/auth/register/          Register new user
POST   /api/auth/token/             Login (get JWT tokens)
POST   /api/auth/token/refresh/     Refresh access token
POST   /api/auth/logout/            Logout
POST   /api/auth/password/reset/    Request password reset
```

#### Flights

```
GET    /api/flights/search/         Search flights
GET    /api/flights/                List saved flights
POST   /api/flights/                Save flight
GET    /api/flights/{id}/           Retrieve flight details
DELETE /api/flights/{id}/           Delete saved flight
GET    /api/flights/history/        Search history
```

#### Hotels

```
GET    /api/hotels/search/          Search hotels
GET    /api/hotels/                 List saved hotels
POST   /api/hotels/                 Save hotel
GET    /api/hotels/{id}/            Retrieve hotel details
DELETE /api/hotels/{id}/            Delete saved hotel
GET    /api/hotels/history/         Search history
```

#### AI Agents

```
POST   /api/agents/execute/         Execute multi-agent system
GET    /api/agents/history/         Agent execution history
GET    /api/agents/{id}/result/     Get agent result
```

#### Bookings

```
GET    /api/bookings/               List user bookings
POST   /api/bookings/               Create booking
GET    /api/bookings/{id}/          Retrieve booking details
PUT    /api/bookings/{id}/          Update booking
DELETE /api/bookings/{id}/          Cancel booking
GET    /api/bookings/{id}/invoice/  Download invoice PDF
```

#### Payments

```
GET    /api/payments/               List payments
POST   /api/payments/               Process payment
GET    /api/payments/{id}/          Payment details
POST   /api/payments/{id}/refund/   Request refund
GET    /api/payment-methods/        List saved cards
POST   /api/payment-methods/        Add payment method
DELETE /api/payment-methods/{id}/   Remove payment method
```

### Authentication

All API requests (except registration and login) require a JWT access token:

```bash
# Include in Authorization header
Authorization: Bearer YOUR_ACCESS_TOKEN

# Example
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  https://demo.eminencetechsolutions.com:3090/api/bookings/
```

### API Examples

<details>
<summary><b>Complete Booking Flow Example</b></summary>

```bash
# 1. Register user
curl -X POST https://demo.eminencetechsolutions.com:3090/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'

# 2. Login
TOKEN=$(curl -X POST https://demo.eminencetechsolutions.com:3090/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }' | jq -r '.access')

# 3. Search flights
curl -X GET "https://demo.eminencetechsolutions.com:3090/api/flights/search/?origin=LAX&destination=JFK&departure_date=2026-08-01&adults=2" \
  -H "Authorization: Bearer $TOKEN"

# 4. Search hotels
curl -X GET "https://demo.eminencetechsolutions.com:3090/api/hotels/search/?location=New%20York&check_in=2026-08-01&check_out=2026-08-05&adults=2" \
  -H "Authorization: Bearer $TOKEN"

# 5. Create booking
BOOKING_ID=$(curl -X POST https://demo.eminencetechsolutions.com:3090/api/bookings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": 123,
    "hotel_id": 456,
    "travelers": [
      {"first_name": "John", "last_name": "Doe", "email": "john@example.com"}
    ],
    "total_amount": 850.00
  }' | jq -r '.id')

# 6. Process payment
curl -X POST https://demo.eminencetechsolutions.com:3090/api/payments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": '$BOOKING_ID',
    "amount": 850.00,
    "payment_method_id": "pm_test_card"
  }'

# 7. Get booking confirmation
curl -X GET "https://demo.eminencetechsolutions.com:3090/api/bookings/$BOOKING_ID/" \
  -H "Authorization: Bearer $TOKEN"
```

</details>

---

## 🚢 Deployment

### Docker Deployment

**Production Docker Compose**:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - NODE_ENV=production

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=yourdomain.com
    command: gunicorn travel_agent.wsgi:application --bind 0.0.0.0:8000 --workers 4

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
```

### Production Setup

#### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Application Deployment

```bash
# Clone repository
git clone https://github.com/your-username/ai-smart-flight-agent.git
cd ai-smart-flight-agent

# Configure production environment
cp .env.example .env.prod
nano .env.prod

# Set production values:
# DEBUG=False
# ALLOWED_HOSTS=yourdomain.com
# STRIPE_SECRET_KEY=sk_live_... (live key!)
# STRIPE_PUBLISHABLE_KEY=pk_live_...

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

#### 3. SSL Configuration

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (cron job)
sudo crontab -e
# Add: 0 0 * * * certbot renew --quiet
```

#### 4. Monitoring Setup

```bash
# Install monitoring tools
docker run -d --name prometheus -p 9090:9090 prom/prometheus
docker run -d --name grafana -p 3000:3000 grafana/grafana

# Configure Prometheus to scrape Django metrics
# Configure Grafana dashboards
```

---

## ⚙️ Configuration Reference

### Django Settings

<details>
<summary><b>Key Settings</b></summary>

```python
# travel_agent/settings.py

# Security
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL')
    )
}

# Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')

# API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
SERP_API_KEY = os.environ.get('SERP_API_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
```

</details>

### Agent Configuration

<details>
<summary><b>Agent Settings</b></summary>

```python
# apps/agents/config.py

AGENT_CONFIG = {
    'MODEL': 'gpt-4o-mini',
    'TEMPERATURE': 0.7,
    'MAX_TOKENS': 1000,
    'TIMEOUT': 30,  # seconds
}

GOAL_AGENT_CONFIG = {
    'BUDGET_PENALTY_MULTIPLIER': 0.1,
    'BUDGET_BONUS_MULTIPLIER': 0.05,
    'BASE_SCORE_WITHIN_BUDGET': 20,
    'BASE_SCORE_OVER_BUDGET': -20,
}

UTILITY_AGENT_CONFIG = {
    'PRICE_WEIGHT': 0.5,
    'RATING_WEIGHT': 0.5,
    'MIN_UTILITY_SCORE': -80,
    'MAX_UTILITY_SCORE': 80,
}
```

</details>

---

## 🛠️ Troubleshooting

### Common Issues

<details>
<summary><b>Port Already in Use</b></summary>

**Problem**: Error starting services due to port conflicts

**Solution**:
```bash
# Find process using port
lsof -i :3090

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml and .env
```

</details>

<details>
<summary><b>Database Connection Error</b></summary>

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Verify DATABASE_URL in .env
```

</details>

<details>
<summary><b>Migration Errors</b></summary>

**Problem**: `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solution**:
```bash
# Clear database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend python manage.py migrate

# Or fake migrations
docker-compose exec backend python manage.py migrate --fake
```

</details>

<details>
<summary><b>Celery Not Processing Tasks</b></summary>

**Problem**: Async tasks not running

**Solution**:
```bash
# Check Celery worker status
docker-compose logs celery-worker

# Restart Celery
docker-compose restart celery-worker celery-beat

# Check RabbitMQ
docker-compose logs rabbitmq
open http://demo.eminencetechsolutions.com:15673  # RabbitMQ management UI
```

</details>

<details>
<summary><b>API Returns 500 Error</b></summary>

**Problem**: Internal server error on API requests

**Solution**:
```bash
# Check backend logs
docker-compose logs backend -f

# Enable Django debug mode temporarily
# Edit .env: DEBUG=True
docker-compose restart backend

# Check for missing migrations
docker-compose exec backend python manage.py showmigrations
```

</details>

### Health Checks

```bash
# Backend health (via nginx)
curl https://demo.eminencetechsolutions.com:3090/api/health

# Expected response:
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "celery": "ok"
}

# MCP Server health (via nginx)
curl https://demo.eminencetechsolutions.com:3090/mcp/health

# RabbitMQ Management UI
open http://demo.eminencetechsolutions.com:15673
# Default credentials: guest / guest
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest && npm test`
5. **Commit**: `git commit -m "feat: add amazing feature"`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Maintenance tasks

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Follow Airbnb style guide, use Prettier
- **Type hints**: Required for all Python functions
- **Documentation**: Add docstrings to all functions

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 AI Smart Flight Agent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **LangChain** - AI framework
- **LangGraph** - Agent orchestration
- **OpenAI** - GPT-4 model
- **SerpAPI** - Search data
- **Stripe** - Payment processing
- **Django** - Web framework
- **React** - UI framework

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/ai-smart-flight-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ai-smart-flight-agent/discussions)

---

<div align="center">

**Built with ❤️ using Multi-Agent AI Architecture**

[⬆ Back to Top](#-ai-smart-flight-agent---comprehensive-documentation)

</div>
