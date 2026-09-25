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

To open it from a phone on the same network, run
`python manage.py runserver 0.0.0.0:8000` and browse to the machine's IP.

## Tests

```bash
DJANGO_DEBUG=1 python manage.py test
```

UI changes are also checked in a headless browser at phone, tablet and desktop
sizes: see `tests/ui/README.md`.

## Deploying

Render runs `build.sh` (install, `collectstatic`) and then `start.sh`
(migrate, `collectstatic`, resume lookups, Gunicorn); `render.yaml` describes
the service and pushes to `main` deploy it. SQLite lives on a mounted disk.
There is no Docker setup. Environment variables, rollback and backups are in
`docs/deployment.md`.

## Management commands

```bash
python manage.py fetch_meanings              # fill in every missing meaning
python manage.py fetch_meanings --list-id 4  # just one list
python manage.py resume_lookups              # requeue lookups a restart interrupted
```

## Layout

One Django project with server-rendered templates:

```
config/          settings, urls, wsgi
vocab/           the app: models, views, forms, tasks, tests
templates/       pages, all extending base.html
static/          app.css, game.js (card stack), dashboard.js
tests/ui/        headless-browser viewport check
docs/            requirements, architecture, API, security, deployment, roadmap
tasks/           backlog, active, completed
wordlists/       ready-to-upload word files
scripts/         offline helpers: PDF to word list, file splitter
.claude/         agent definitions and skills for the development workflow
```

## How work is organized

- `CLAUDE.md` is the control document: stack, commands, rules, and what needs the owner's approval.
- `tasks/active.md` holds what is being worked on now, `tasks/backlog.md` what is next, `tasks/completed.md` what is done and how it was verified.
- `docs/` is the shared knowledge base; `docs/test-reports/` holds test reports.
- Work moves through specialised agents in `.claude/agents/`: **planner** (turns a request into tasks with acceptance criteria), **architect** (fits the change into the existing design), **developer** (implements it), **tester** (verifies it, including mobile viewports), **security** (reviews it), **deployer** (checks and, after approval, ships it). Small changes skip stages; database, security and production changes use all of them. Each agent hands off through files in the repository, and pushing to `main` (a deploy) always waits for the owner.
