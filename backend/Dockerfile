FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in stages to avoid resolution-too-deep errors
COPY requirements.txt .
RUN pip install --upgrade pip && \
    # Stage 1: Core Django and database
    pip install Django==5.0.1 djangorestframework==3.14.0 django-cors-headers==4.3.1 \
                django-filter==23.5 django-environ==0.11.2 psycopg2-binary==2.9.9 \
                dj-database-url==2.1.0 && \
    # Stage 2: Celery and task queue
    pip install redis==5.0.1 celery==5.3.6 django-celery-beat==2.7.0 \
                django-celery-results==2.5.1 kombu==5.3.5 && \
    # Stage 3: Authentication and security
    pip install djangorestframework-simplejwt==5.3.1 django-allauth==0.61.1 \
                PyJWT==2.8.0 cryptography==42.0.2 && \
    # Stage 4: Web servers
    pip install gunicorn==21.2.0 uvicorn==0.27.0 websockets==12.0 \
                channels==4.0.0 channels-redis==4.2.0 daphne==4.1.0 && \
    # Stage 5: AI/ML frameworks (complex dependencies)
    # Install langchain with updated versions for better pydantic compatibility
    pip install langchain-core==0.2.38 langchain==0.2.16 && \
    pip install langchain-openai==0.1.23 langchain-community==0.2.16 \
                langgraph==0.0.32 openai==1.54.4 langsmith==0.1.75 && \
    # Stage 6: Vector DB and embeddings
    pip install "chromadb>=0.4.22,<0.5.0" "sentence-transformers>=2.3.1,<3.0.0" \
                langchain-chroma>=0.1.0 && \
    # Stage 7: Data processing
    pip install pandas==2.2.0 numpy==1.26.3 python-dateutil==2.8.2 && \
    # Stage 8: API integrations and utilities
    pip install google-search-results==2.4.2 stripe==8.0.0 requests==2.31.0 \
                httpx==0.26.0 python-dotenv==1.0.1 pydantic==2.6.0 \
                pydantic-settings==2.1.0 && \
    # Stage 9: AWS and email services
    pip install boto3==1.34.34 sendgrid==6.11.0 icalendar==5.0.11 && \
    # Stage 10: Monitoring and debugging
    pip install sentry-sdk==1.40.0 django-debug-toolbar==4.3.0 \
                python-json-logger==2.0.7 colorlog==6.8.2 && \
    # Stage 11: Testing frameworks
    pip install "pytest>=8.0.0" "pytest-django>=4.7.0" "pytest-cov>=4.1.0" \
                "factory-boy>=3.3.0" && \
    # Stage 12: Code quality and documentation
    pip install black==24.1.1 flake8==7.0.0 isort==5.13.2 \
                drf-spectacular==0.27.1 && \
    # Stage 13: PDF generation and parsing
    pip install reportlab==4.0.9 qrcode==7.4.2 Pillow==10.2.0 \
                beautifulsoup4==4.12.3 lxml==5.1.0

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Collect static files will be done in docker-compose command

# Run migrations will be done in docker-compose command

EXPOSE 8109

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "travel_agent.wsgi:application", "--bind", "0.0.0.0:8109", "--workers", "4", "--timeout", "120"]
