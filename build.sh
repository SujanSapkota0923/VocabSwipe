#!/usr/bin/env bash
# Build step for deploying VocabSwipe.
set -o errexit

pip install -r requirements.txt

# Static files are baked into the image at build time. WhiteNoise serves them
# from STATIC_ROOT at runtime; without this step the game page loads but
# game.js 404s and no cards ever appear.
python manage.py collectstatic --noinput

# Migrations are NOT run here on purpose: the persistent disk holding the
# database is only mounted at runtime, so migrating during the build would
# write to a throwaway file. See start.sh.
