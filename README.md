# VocabSwipe

Learn words by swiping cards. Right for the words you know, left for the ones
you don't. Upload your own list or play one someone else shared — no account
needed for public lists.

Django 4.2, SQLite, WhiteNoise, no frontend build step and no CDN.

## What it does

- **Swipe to learn.** Classic mode, or timer mode where a card you leave too
  long counts as one to review.
- **Spaced repetition.** Every answer schedules the word with SM-2, so review
  mode shows only what is actually due.
- **Your own lists.** Upload `.csv`, `.txt`, `.tsv` or `.xlsx`. A file of bare
  words works too — the definitions are looked up from
  [dictionaryapi.dev](https://dictionaryapi.dev/) in the background.
- **Sharing.** Every list gets a six-character code. Make a list public and
  anyone can play it without signing up.
- **Guests.** Signed out, progress is kept in the browser; signing up carries
  the unlocked lists over.
- **A starter deck.** A public list of common words ships with the database
  migrations, so a brand new install has something to play immediately.

## File format

One word per line. The meanings are optional:

```
word
word, a meaning
word, first meaning; second meaning; third meaning
```

A header row is skipped, quoted commas are kept, repeated words are collapsed,
and at most three meanings per word are stored. Spreadsheets use the first
column for the word and the second for the meanings.

## Running it locally

```bash
pip install -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000. The starter deck is playable straight away.

Run the tests with:

```bash
DJANGO_DEBUG=1 python manage.py test
```

## Deploying

`build.sh` installs dependencies and collects static files. `start.sh` runs
migrations and starts gunicorn; it is the process to run, not gunicorn
directly. `render.yaml` describes the whole service for Render, and the same
two commands work on any host.

Environment variables (see `.env.example`):

| Variable | Needed | Notes |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | yes | The app refuses to start without it when `DEBUG` is off |
| `DJANGO_DEBUG` | yes | `0` in production |
| `DJANGO_DB_PATH` | yes | Point at a persistent disk, e.g. `/var/lib/vocabswipe/db.sqlite3`, or every deploy wipes the uploaded lists |
| `DJANGO_ALLOWED_HOSTS` | yes | Comma separated |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | yes | Comma separated, with scheme |
| `DJANGO_SECURE_SSL_REDIRECT` | no | `0` when Cloudflare or a proxy already forces HTTPS |

Two things are worth knowing:

- Static files are served by WhiteNoise from `STATIC_ROOT`. If `collectstatic`
  does not run during the build, `game.js` 404s and the game shows no cards.
  `build.sh` runs it.
- SQLite is kept on a mounted disk. Without one, a deploy replaces the code
  directory and every uploaded word list disappears.

## Management commands

```bash
python manage.py fetch_meanings              # fill in every missing meaning
python manage.py fetch_meanings --list-id 4  # just one list
python manage.py resume_lookups              # requeue lookups a restart interrupted
```

`start.sh` runs `resume_lookups` at boot. The dashboard also restarts a
waiting lookup when its owner opens the page.

## Layout

```
config/          settings, urls, wsgi
vocab/           the app: models, views, forms, tasks, tests
  utils/         file parsing and the dictionary API client
  management/    fetch_meanings, resume_lookups
templates/       pages, all extending base.html
static/css/      one hand written stylesheet, no framework
static/js/       game.js (the card stack) and dashboard.js (upload, polling)
docs/            architecture, API, security, deployment, roadmap
wordlists/       ready-to-upload word files
scripts/         offline helpers: PDF to word list, file splitter
```

## Documentation

- `Plan.md` — project state, known issues, task roadmap, next task
- `docs/ARCHITECTURE.md` — request flow, import pipeline, models, feature inventory
- `docs/API.md` — JSON and form endpoints
- `docs/SECURITY.md` — security audit and open findings
- `docs/DEPLOYMENT.md` — build, start, Render, data and logs
- `docs/ROADMAP.md` — the long-term development brief the plan is based on
- `wordlists/README.md`, `scripts/README.md` — sample word files and offline helpers
