# Shortcuts for the common tasks. Everything runs inside the local .venv,
# so no shell activation is needed.
PYTHON := .venv/bin/python

.PHONY: help dev setup demo run test check superuser clean up down logs docker-demo docker-superuser

help:
	@echo "Local development"
	@echo "  make dev         everything at once: environment, demo data and server"
	@echo "  make setup       create the virtualenv, install, configure and migrate"
	@echo "  make demo        same as setup, plus a small demo dataset"
	@echo "  make run         start the development server"
	@echo "  make test        run the test suite"
	@echo "  make check       run Django's system checks"
	@echo "  make superuser   create an administrator account"
	@echo "  make clean       remove the virtualenv, the database and caches"
	@echo
	@echo "Containers (PostgreSQL + gunicorn)"
	@echo "  make up          build and start the stack in the background"
	@echo "  make down        stop it"
	@echo "  make logs        follow the application logs"
	@echo "  make docker-demo load the demo dataset inside the container"

# --- local ---------------------------------------------------------------
dev: demo
	@echo
	@echo "Starting the server. Create an account in another terminal with 'make superuser'."
	$(PYTHON) manage.py runserver

setup:
	./scripts/setup.sh

demo:
	./scripts/setup.sh --demo

run:
	$(PYTHON) manage.py runserver

test:
	$(PYTHON) manage.py test

check:
	$(PYTHON) manage.py check

superuser:
	$(PYTHON) manage.py createsuperuser

clean:
	rm -rf .venv db.sqlite3 staticfiles
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

# --- containers ----------------------------------------------------------
up:
	docker compose up --build -d
	@echo "Running at http://127.0.0.1:8000/ — 'make logs' to follow, 'make down' to stop."

down:
	docker compose down

logs:
	docker compose logs -f web

docker-demo:
	docker compose exec web python manage.py seed_demo

docker-superuser:
	docker compose exec web python manage.py createsuperuser
