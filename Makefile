# Makefile at project root

# Use this variable so we don't repeat the docker-compose file path
DOCKER_COMPOSE_FILE = docker-compose.yml

.PHONY: help
help:  ## Show this help message
	@echo "Commonly used make targets:"
	@echo "  make build            - Build images"
	@echo "  make up               - Bring up containers in the background"
	@echo "  make down             - Stop and remove containers"
	@echo "  make logs             - Follow logs"
	@echo "  make ps               - List running containers"
	@echo "  make restart          - Rebuild and restart containers in one go"
	@echo "  make resetdb          - Remove volumes and re-up (destroys local DB data!)"
	@echo "  make migrate          - Run Django migrations inside the backend container"
	@echo "  make collectstatic    - Run Django collectstatic inside the backend container"
	@echo "  make shell            - Open a Bash shell in the backend container"
	@echo "  make dbshell          - Open psql in the db container"

## -----------------------------
## Docker Compose Targets
## -----------------------------

build:  ## Build Docker images
	docker-compose -f $(DOCKER_COMPOSE_FILE) build

up:  ## Run containers in the background
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d

down:  ## Stop and remove containers
	docker-compose -f $(DOCKER_COMPOSE_FILE) down

logs:  ## Follow logs
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f

ps:  ## Show container status
	docker-compose -f $(DOCKER_COMPOSE_FILE) ps

restart: down build up logs  ## Rebuild and restart containers in one go

resetdb:  ## Remove volumes, then re-up (DESTROYS local DB data!)
	@echo "WARNING: This will remove your named volumes and destroy any local DB data."
	@echo "Press CTRL+C to cancel or wait 5 seconds to continue."
	sleep 5
	docker-compose -f $(DOCKER_COMPOSE_FILE) down -v
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d

migrate:  ## Run Django migrations inside the backend container
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec backend poetry run python manage.py migrate

collectstatic:  ## Collect Django static files inside the backend container
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec backend poetry run python manage.py collectstatic --noinput

shell:  ## Open a Bash shell in the django container
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec django bash

dbshell:  ## Open psql shell in the db container (adjust user/db if needed)
	docker-compose -f $(DOCKER_COMPOSE_FILE) exec db psql -U careacross_admin -d careacross-backend