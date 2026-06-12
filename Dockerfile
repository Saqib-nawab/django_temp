FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static assets at build time so WhiteNoise can serve them
RUN DJANGO_SECRET_KEY=build-only-key python manage.py collectstatic --noinput

# Run as an unprivileged user
RUN useradd --create-home appuser \
    && mkdir -p /app/media \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "django_practice.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
