# VocabSwipe — Project Instructions

Read this file first in every session. It is the control document for the
project and for the agents in `.claude/agents/`. Details live in `docs/`; work
items live in `tasks/`.

Last verified against the repository: 2026-09-25.

## Project identity

VocabSwipe turns vocabulary files into swipeable flash-card decks. A user
uploads a word list, plays it card by card (right = know, left = review), and
every answer is scheduled with SM-2 so review mode shows only due words. Lists
can be shared by a six-character code or made public; guests can play public
or unlocked lists without an account. Words uploaded without a meaning get one
from dictionaryapi.dev in a background thread. Primary audience: students
preparing for PTE and other English exams, mostly on phones.

The app does not use AI. Do not describe the review algorithm as AI.

## Technology stack (verified)

| Area | What the repository uses |
| --- | --- |
| Backend | Python 3.12, Django 4.2 (pinned 4.2.30 — **out of support since April 2026**, see FIX-003) |
| Frontend | Django templates, one hand-written stylesheet (`static/css/app.css`), vanilla JS (`static/js/game.js`, `static/js/dashboard.js`). No framework, no build step, no CDN |
| Database | SQLite in WAL mode (`vocab/apps.py`), on a persistent disk in production |
| Cache | None configured (Django default local-memory) |
| Authentication | Django sessions and `django.contrib.auth` (username + password) |
| APIs | Five JSON endpoints under `/api/` plus form POSTs — `docs/api.md` |
| Background work | In-process daemon thread (`vocab/tasks.py`); no queue |
| External services | dictionaryapi.dev (no key) |
| Testing | Django `TestCase` suite in `vocab/tests.py`; optional headless-browser viewport check in `tests/ui/` |
| Static files | WhiteNoise, `CompressedManifestStaticFilesStorage` |
| Containerization | None. There is no Dockerfile or `docker-compose.yml` |
| Deployment | Render web service (`render.yaml`), Gunicorn via `start.sh`, Cloudflare in front of the custom domain |
| CI/CD | None. Render deploys from `main` |

Do not add a technology to this table until it exists in the repository.

## Repository map

```
config/                 settings, root URLs, wsgi/asgi
vocab/                  the Django app: models, views, forms, tasks, admin, tests
  utils/                upload parser, dictionary API client
  management/commands/  fetch_meanings, resume_lookups
  migrations/           0001–0009 (0009 ships the public starter deck)
templates/              pages; base.html holds the header, tab bar and icon sprite
static/                 css/app.css, js/game.js, js/dashboard.js, favicon.svg
tests/ui/               headless-Chromium viewport check (not part of manage.py test)
docs/                   shared knowledge base (see "Documentation")
tasks/                  backlog.md, active.md, completed.md
wordlists/              ready-to-upload word files
scripts/                offline helpers (PDF → word list, file splitter)
.claude/agents/         planner, architect, developer, tester, security, deployer
.claude/skills/         reusable instruction packages (none yet, see README)
build.sh, start.sh      build step and runtime entrypoint
render.yaml, Procfile   deployment descriptors
```

VocabSwipe is a single Django project with server-rendered templates. There is
no separate `backend/` or `frontend/` and none should be created: backend work
is `config/` and `vocab/`, frontend work is `templates/` and `static/`.

## Commands

```bash
pip install -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py runserver                     # 0.0.0.0:8000 to reach it from a phone
DJANGO_DEBUG=1 python manage.py test           # full suite
DJANGO_DEBUG=1 python manage.py makemigrations --check --dry-run
DJANGO_DEBUG=0 DJANGO_SECRET_KEY=<random> python manage.py check --deploy
DJANGO_DEBUG=0 DJANGO_SECRET_KEY=<random> python manage.py collectstatic --noinput
python manage.py fetch_meanings [--list-id N]  # fill missing meanings
python manage.py resume_lookups                # reset interrupted lookups
```

There is no linter or type checker configured. Browser checks: `tests/ui/README.md`.

## Environment variables

| Variable | Default | Notes |
| --- | --- | --- |
| `DJANGO_DEBUG` | off | `1` for local development |
| `DJANGO_SECRET_KEY` | falls back to a hard-coded test string (FIX-006) | Must be set in production |
| `DJANGO_ALLOWED_HOSTS` | `*` in debug; production domains + localhost otherwise | `RENDER_EXTERNAL_HOSTNAME` is appended automatically |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | production domains (https) | With scheme |
| `DJANGO_DB_PATH` | `BASE_DIR/db.sqlite3` | Persistent disk in production |
| `DJANGO_SECURE_SSL_REDIRECT` | on | `0` behind Render/Cloudflare |
| `PORT`, `WEB_CONCURRENCY` | 8000, 3 | Read by `start.sh` |

A `.env` file is tracked in git (FIX-007). Never read, print or copy secret
values into docs, logs, tasks or commits.

## Development principles

- Preserve existing functionality. Understand the code before changing it.
- Prefer small, reviewable changes; one task per change; no unrelated refactoring.
- Follow existing conventions: function views, plain templates, no inline JS frameworks, hand-written CSS with the tokens in `:root`.
- Do not add dependencies unless the task cannot reasonably be done without them.
- Do not expose secrets. Do not commit `.env` files containing secrets.
- Run the relevant tests after every change; report failures with their output.
- UI work is mobile first: check 320, 375, 390 and 430 px, then tablet and desktop. Respect safe areas, `100dvh`, touch targets (≥ 44 px), keyboard use and reduced motion.
- Keep production changes controlled (see "Human approval").
- When docs disagree with code, fix the docs, not the code.
- Document meaningful architectural decisions in `docs/architecture.md` → Decisions.

## Agent workflow

Agents are defined in `.claude/agents/`. Each owns one stage and hands off
through files in the repository, not conversation memory.

| Stage | Agent | Writes |
| --- | --- | --- |
| Planning | `planner` | `tasks/backlog.md`, `tasks/active.md` |
| Architecture | `architect` | `docs/architecture.md`, `docs/architecture-<topic>.md` |
| Implementation | `developer` | source code (reviewed as a git diff) |
| Testing | `tester` | `vocab/tests.py`, `tests/`, `docs/test-reports/` |
| Security review | `security` | `docs/security.md` |
| Deployment | `deployer` | `docs/deployment.md` |

Choose the stages a task needs:

- Documentation change: developer → review → completed.
- Small UI or bug fix: planner (short) → developer → tester → completed.
- New feature: planner → architect → developer → tester → security → completed.
- Database, auth, upload, settings or production change: planner → architect → developer → tester → security → human approval → deployer → verification → completed.

### Task lifecycle

`BACKLOG → PLANNED → ARCHITECTURE REVIEW → IMPLEMENTATION → TESTING → SECURITY
REVIEW → READY FOR DEPLOYMENT → DEPLOYED → VERIFIED → COMPLETED`

Skip stages that do not apply and say which were skipped. A task moves to
`tasks/completed.md` only after its acceptance criteria were verified — never
because code was written.

### Handoff rules

- Every agent reads this file and the task in `tasks/active.md` first.
- Every agent checks the previous agent's actual output (files, diff, test run) instead of trusting its summary.
- Source of truth when things conflict: 1) code, 2) database schema and migrations, 3) automated tests, 4) the current task, 5) docs, 6) agent assumptions.
- Problems are recorded, not hidden: problem, cause, impact, what was tried, current state, recommended next action. A blocking problem stops the task.

### Concurrency

Agents that edit files run one after another. Parallel work is allowed only
when the file sets do not overlap (for example documentation in `docs/` while
code changes in `vocab/`). Two agents never edit the same file at once.

## Git rules

- Check `git status` and the current diff before starting; never discard uncommitted work.
- Never run `git reset --hard`, `git clean -fd`, force pushes, or delete migrations unless the owner asks.
- Inspect `git diff` and `git status` after every change.
- `main` deploys to production on Render. Use a branch (`feature/…`, `fix/…`, `refactor/…`) for work that is not ready to ship; trivial doc edits can go straight to `main` when the owner commits them.
- Commit only when the owner asks. No AI attribution in commits, pull requests or files.

## Human approval

Ask the owner before:

- pushing to `main` or deploying (that is the same thing here);
- migrations that drop or rewrite data, or any change to existing migrations;
- deleting user data, lists, the database file or the Render disk;
- changing or rotating secrets, `render.yaml` env values, DNS or Cloudflare settings;
- removing a user-facing feature;
- large rewrites or new frameworks.

Agents may prepare, explain and validate these changes; the owner decides.

## Must not change without review

- Migrations `0001`–`0009`, especially the data migrations `0005` and `0009`.
- `WordList.share_code` format and uniqueness (codes are already shared).
- The upload file format in `README.md`.
- The `build.sh` / `start.sh` split (migrations run at start because the disk is only mounted at runtime) and `collectstatic` in both.
- `DJANGO_DB_PATH` on the persistent disk; the SQLite WAL pragmas in `vocab/apps.py`.
- The `if not DEBUG:` security block in `config/settings.py`.
- Guest progress (session codes + `localStorage`) and the signup carry-over.
- Element ids in `templates/game.html` and `templates/dashboard.html` that the JS depends on.

## Documentation

| File | Contents |
| --- | --- |
| `docs/requirements.md` | Product purpose, verified functional and non-functional requirements, user flows |
| `docs/architecture.md` | System overview, pipeline, data model, feature inventory, decisions |
| `docs/api.md` | JSON and form endpoints |
| `docs/security.md` | Security audit and open findings |
| `docs/deployment.md` | Local, Render, migrations, health, rollback, backups, logs |
| `docs/roadmap.md` | The long-term development brief (formerly root `claude.md`); where it says "CLAUDE.md" it means this file and `tasks/` |
| `docs/test-reports/` | Test reports per task |
| `tasks/*.md` | Backlog, active and completed work |

## Current state

- Active: UI-001 (mobile-first UI/UX) — deployed, awaiting owner sign-off and a real-device check. See `tasks/active.md`.
- Next pending: FIX-006 and FIX-007 (owner decisions), then FIX-003 (Django 5.2 LTS). See `tasks/backlog.md`.
