#!/usr/bin/env bash
# Runtime entrypoint. Runs with the persistent disk mounted.
set -o errexit

python manage.py migrate --noinput

# A lookup interrupted by the previous shutdown goes back in the queue.
python manage.py resume_lookups

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-3}" \
    --timeout 120
