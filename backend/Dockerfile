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
    # Stage 2: AI/ML frameworks (complex dependencies)
    pip install langchain==0.1.6 langchain-openai==0.0.5 langchain-community==0.0.19 \
                langgraph==0.0.23 openai==1.12.0 langsmith>=0.0.83 && \
    # Stage 3: Vector DB and embeddings
    pip install "chromadb>=0.4.22,<0.5.0" "sentence-transformers>=2.3.1,<3.0.0" \
                langchain-chroma>=0.1.0 && \
    # Stage 4: Everything else from requirements.txt
    pip install -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Collect static files will be done in docker-compose command

# Run migrations will be done in docker-compose command

EXPOSE 8109

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "travel_agent.wsgi:application", "--bind", "0.0.0.0:8109", "--workers", "4", "--timeout", "120"]
