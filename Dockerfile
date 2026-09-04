# Image for the Center Management application.
#
#   docker compose up --build
#
# Runs gunicorn as an unprivileged user, with WhiteNoise serving the static
# files, so the container needs nothing in front of it to be usable.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first: this layer is cached until the requirements change.
COPY requirements.txt requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

# Collect the static files at build time; DEBUG is irrelevant here, but the
# settings module refuses to load without a key.
RUN DJANGO_SECRET_KEY=build-time-only python manage.py collectstatic --no-input

RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --no-input && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -"]
