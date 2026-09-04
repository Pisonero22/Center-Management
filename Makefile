# Shortcuts for the common tasks. Everything runs inside the local .venv,
# so no shell activation is needed.
PYTHON := .venv/bin/python

.PHONY: help setup demo run test check superuser clean

help:
	@echo "make setup      create the virtualenv, install, configure and migrate"
	@echo "make demo       same as setup, plus a small demo dataset"
	@echo "make run        start the development server"
	@echo "make test       run the test suite"
	@echo "make check      run Django's system checks"
	@echo "make superuser  create an administrator account"
	@echo "make clean      remove the virtualenv, the database and caches"

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
	rm -rf .venv db.sqlite3
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
