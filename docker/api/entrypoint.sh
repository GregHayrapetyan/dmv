#!/bin/sh
set -eu

echo "Waiting for database at ${DB_HOST:-db}:${DB_PORT:-5432}..."
until python - <<'PY'
import os, socket, sys
host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))
try:
    with socket.create_connection((host, port), timeout=2):
        sys.exit(0)
except OSError:
    sys.exit(1)
PY
do
  sleep 1
done
echo "Database is reachable."

python manage.py migrate --noinput

python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dmv.settings")
django.setup()

from django.core.management import call_command
from django.db import connection

tables = connection.introspection.table_names()
if "cache_table" in tables:
    print("cache table already exists")
else:
    call_command("createcachetable")
PY

python manage.py collectstatic --noinput

exec gunicorn dmv.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile "-" \
  --error-logfile "-"
