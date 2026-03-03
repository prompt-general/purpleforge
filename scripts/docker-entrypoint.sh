#!/bin/bash
set -e

echo "Waiting for PostgreSQL to become available..."
until python -c "import psycopg2; from app.core.config import settings; psycopg2.connect(settings.DATABASE_URL)" >/dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL started"

echo "Initializing database..."
python -m app.db.init_db

echo "Starting command..."
exec "$@"
