.PHONY: help build up down logs clean restart shell-backend shell-frontend migrate createsuperuser test

help:
	@echo "AI Travel Agent - Make Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make clean          - Stop and remove all containers and volumes"
	@echo "  make restart        - Restart all services"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-frontend - Open shell in frontend container"
	@echo "  make migrate        - Run Django migrations"
	@echo "  make createsuperuser - Create Django superuser"
	@echo "  make test           - Run backend tests"

build:
	docker compose build

up:
	./start.sh

down:
	./stop.sh

logs:
	docker compose logs -f

clean:
	docker compose down -v
	rm -rf backend/staticfiles/*
	rm -rf backend/media/*
	rm -rf frontend/node_modules
	rm -rf frontend/dist

restart:
	docker compose restart

shell-backend:
	docker compose exec backend /bin/bash

shell-frontend:
	docker compose exec frontend /bin/sh

migrate:
	docker compose exec backend python manage.py migrate

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

test:
	docker compose exec backend pytest

collectstatic:
	docker compose exec backend python manage.py collectstatic --noinput

db-reset:
	docker compose down
	docker volume rm ai-smart-flight-agent_postgres_data
	docker compose up -d postgres
	@echo "Waiting for database to be ready..."
	@sleep 10
	docker compose up -d backend
	@sleep 5
	make migrate
	@echo "Database reset complete!"
