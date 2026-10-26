#!/usr/bin/env bash
# Build script for hosting (Render and similar). Run with: bash build.sh
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py makemigrations accounts shop workouts --noinput
python manage.py migrate --noinput

# Optional: load demo products and exercises on first deploy (set SEED_DEMO=1)
if [ "${SEED_DEMO:-0}" = "1" ]; then
  python manage.py seed_demo
fi

# Optional: create the admin user from env vars (set DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD)
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py createsuperuser --noinput --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
fi
