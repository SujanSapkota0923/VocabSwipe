#!/usr/bin/env bash
# Runtime entrypoint. Runs with the persistent disk mounted.
set -o errexit

python manage.py migrate --noinput

# Also run by build.sh. Repeated here because a host whose build command is
# not build.sh ships without the static manifest, and then every page that
# uses {% static %} is a 500. Takes a few seconds and is a no-op when current.
python manage.py collectstatic --noinput

# A lookup interrupted by the previous shutdown goes back in the queue.
python manage.py resume_lookups

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-3}" \
    --timeout 120
