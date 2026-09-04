#!/usr/bin/env bash
# Set up a working development environment from a fresh clone:
# virtualenv, dependencies, .env with a generated secret key, and the database.
#
#   ./scripts/setup.sh          environment only
#   ./scripts/setup.sh --demo   also load the demo dataset
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV=".venv"

if [ ! -x "$VENV/bin/python" ]; then
  echo "==> Creating virtual environment in $VENV"
  "$PYTHON_BIN" -m venv "$VENV"
fi

echo "==> Installing dependencies"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r requirements.txt

if [ ! -f .env ]; then
  echo "==> Writing .env with a generated secret key"
  KEY=$("$VENV/bin/python" -c "from django.core.management.utils import get_random_secret_key as k; print(k())")
  {
    echo "DJANGO_SECRET_KEY=$KEY"
    echo "DJANGO_DEBUG=true"
    echo "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1"
  } > .env
else
  echo "==> .env already exists, leaving it alone"
fi

echo "==> Applying migrations"
"$VENV/bin/python" manage.py migrate --no-input

if [ "${1:-}" = "--demo" ]; then
  echo "==> Loading demo data"
  "$VENV/bin/python" manage.py seed_demo
fi

# An account can be created without prompts by exporting the usual Django
# variables, which is what a CI job or a container would do:
#   DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=... ./scripts/setup.sh
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  echo "==> Creating superuser ${DJANGO_SUPERUSER_USERNAME}"
  "$VENV/bin/python" manage.py createsuperuser --no-input \
    --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
fi

echo
echo "Done. Next steps:"
echo "  make superuser   # create an account to sign in with"
echo "  make run         # start the server at http://127.0.0.1:8000/"
