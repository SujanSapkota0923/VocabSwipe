# VocabSwipe Plan

Persistent project state: what VocabSwipe is, what has been verified, what is
next. Read this before starting work. `claude.md` holds the full roadmap brief
this plan is derived from; the detailed references live in `docs/`.

Last updated: 2026-09-25 (UI-001).

## Project Overview

VocabSwipe turns vocabulary files into swipeable flash-card decks. A user
uploads a word list (`.txt`, `.csv`, `.tsv`, `.xlsx`), plays it card by card
(right = know, left = review), and the app schedules each answer with SM-2 so
review mode shows only due words. Lists can be shared by a six-character code
or made public; guests can play public or unlocked lists without an account.
Words uploaded without a meaning get one from dictionaryapi.dev in a
background thread. Primary audience: PTE and other English-exam students.

## Technology Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.12 (Render pins 3.12.13) |
| Framework | Django 4.2 (pinned 4.2.30; **extended support ended April 2026**) |
| Database | SQLite in WAL mode, on a persistent disk in production |
| Background work | In-process daemon thread (`vocab/tasks.py`), no queue |
| Static files | WhiteNoise, `CompressedManifestStaticFilesStorage` |
| App server | Gunicorn via `start.sh` |
| Frontend | Django templates, one hand-written CSS file, vanilla JS, no build step, no CDN |
| External API | dictionaryapi.dev (no key) |
| Spreadsheet parsing | openpyxl (read-only mode) |
| Hosting | Render (`render.yaml`), custom domain `vocab.sujansapkota07.com.np` |

## Architecture

Monolithic Django project: `config/` (settings, root URLs) and one app,
`vocab/`. Server-rendered pages plus a small JSON API used by `game.js` and
`dashboard.js`. See `docs/ARCHITECTURE.md` for diagrams, the processing
pipeline and where each piece lives.

## Repository Structure

```
config/                 settings.py, urls.py, wsgi/asgi
vocab/                  models, views, forms, tasks, admin, tests
  utils/parsing.py      upload parser (text + xlsx), dedupe, limits
  utils/dictionary_api.py  dictionaryapi.dev client
  management/commands/  fetch_meanings, resume_lookups
  migrations/           0001–0009 (0009 ships the public starter deck)
templates/              base + 6 pages + registration/login, signup
static/css/app.css      single stylesheet
static/js/              game.js (card stack), dashboard.js (upload, polling)
build.sh / start.sh     build step / runtime entrypoint (migrate, resume, gunicorn)
render.yaml, Procfile   deployment
docs/                   ARCHITECTURE, SECURITY, API, DEPLOYMENT
*.py in root            offline one-off helpers (PDF extraction, cleaning, splitting)
*.txt, *.csv, split_files/  sample / source vocabulary data (tracked in git)
AUTO_SPLIT_FEATURE.md, RATE_LIMIT_FIX.md, PDF_CONVERSION_GUIDE.md  stale notes, see Known Issues
```

## Current Features (verified 2026-09-25)

Verified by reading the code and by the passing test suite (43 tests).

- Swipe, button and arrow-key answers; classic and timer mode (3–120 s per card).
- Per-user progress (`WordProgress`) with SM-2 scheduling; review mode hides known words not yet due.
- Daily streak and total reviews (`UserStats`).
- Upload `.txt/.csv/.tsv/.xlsx/.xlsm`, 5 MB cap, 20,000-word cap, header skip, quoted commas, up to 3 meanings, case-insensitive dedupe inside a file.
- Bare-word files: meanings, example and audio URL fetched in a background thread with progress polling; interrupted lookups resume at boot and on dashboard load.
- Sharing: unique share code per list, join by code, public/private toggle, Explore page with search.
- Guest play: unlocked codes kept in the session, known words in `localStorage`; signup carries unlocked lists over.
- Public starter deck ("Everyday English", code `START1`) created by migration 0009.
- Production settings: env-driven secret, debug, hosts, CSRF origins; HTTPS/HSTS/secure cookies when `DEBUG` is off. `check --deploy` reports no issues.

See `docs/ARCHITECTURE.md` → Feature Inventory for partial, broken and missing features.

## Database Models

`WordList`, `Vocabulary`, `WordProgress`, `JoinedList`, `UserStats` plus
Django's `User`. Field-level detail and the review findings are in
`docs/ARCHITECTURE.md` → Database.

## API Structure

Five JSON endpoints under `/api/` plus form-POST page actions. Documented in
`docs/API.md`.

## Vocabulary Processing Pipeline

Upload → form validation → parse (text or xlsx) → clean → dedupe → one
`WordList` + `bulk_create` of `Vocabulary` → optional background meaning
lookup. No automatic 50-word splitting in the app today (it existed in commit
`90be664` and was later removed). PDF support exists only as offline root
scripts. Detail in `docs/ARCHITECTURE.md`.

## Learning / Review System

`WordProgress.apply_review(is_known)` implements SM-2 with right swipe = q4 and
left swipe = q0. Known words get growing intervals; a miss resets to 1 day.
Review mode = every unknown word plus known words whose `next_review_date` has
passed. No session tracking, no NEW/LEARNING/REVIEW/MASTERED states yet.

## Security Architecture

Django auth (session cookies, PBKDF2, default validators), CSRF on every POST
including the JSON endpoint, object checks via `can_play()` and owner-filtered
querysets, uploads parsed in memory and never written to disk. Full audit and
findings in `docs/SECURITY.md`.

## Deployment Architecture

Render web service, `build.sh` (pip install + collectstatic) then `start.sh`
(migrate, resume_lookups, gunicorn with 3 workers). SQLite on a 1 GB mounted
disk. Health check `/explore/`. Detail in `docs/DEPLOYMENT.md`.

## Development Commands

```bash
pip install -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py runserver
DJANGO_DEBUG=1 python manage.py test
DJANGO_DEBUG=1 python manage.py makemigrations --check --dry-run
DJANGO_DEBUG=0 DJANGO_SECRET_KEY=<random> python manage.py check --deploy
python manage.py fetch_meanings [--list-id N] [--pause 0.5]
python manage.py resume_lookups
```

Note: the local environment used during the audit had Django 4.2.0,
requests 2.28.1 and openpyxl 3.1.2 installed, not the pinned versions. Use a
virtualenv built from `requirements.txt`.

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | off | `1` for local development |
| `DJANGO_SECRET_KEY` | none | Required when debug is off; startup fails without it |
| `DJANGO_ALLOWED_HOSTS` | `*` when debug is on; production domain + localhost otherwise | Comma separated |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | production domain (https) | Comma separated, with scheme |
| `DJANGO_DB_PATH` | `BASE_DIR/db.sqlite3` | Must point at the persistent disk in production |
| `DJANGO_SECURE_SSL_REDIRECT` | on | `0` when a proxy already forces HTTPS (Render config uses `0`) |
| `PORT`, `WEB_CONCURRENCY` | 8000, 3 | Read by `start.sh` |

## Testing Strategy

Django `TestCase` suite in `vocab/tests.py` (43 tests, all passing on
2026-09-25): pages, card API, uploads, parsing, lookup recovery, SM-2, list
management, starter deck. Network calls are mocked. Not yet covered: invalid
IDs, IDOR on every endpoint, rate limits, xlsx resource limits, large imports,
timer-mode JS. No JS tests.

## Known Issues

Confirmed during the audit:

1. ~~Invalid or oversized ids return 500~~ — fixed in FIX-002.
2. Django 4.2 is past end of support (April 2026). No more security releases.
3. No rate limiting anywhere: login, signup, share-code guessing (`/game/?code=`, join forms), uploads, card status POSTs.
4. `/api/cards/` returns every playable card in one response, `order_by('?')`, no limit. "Play all" across big lists sends thousands of rows.
5. Dashboard runs one query per list (`decorate()`) and loads every known word ID into memory.
6. The background thread's duplicate guard is per process; with 3 Gunicorn workers two workers can look up the same list at once. Threads die with the worker.
7. Words with no dictionary entry are saved with the placeholder text `No definition found for "…"` as `meaning_1`, which is indistinguishable from real data afterwards.
8. `MAX_WORDS` truncates at 20,000 silently; the user is not told words were dropped.
9. "Review N" on the dashboard counts unknown words, but review mode also serves due known words, so the numbers differ.
10. ~~Card front hint says "Swipe to reveal"~~ — fixed in UI-001 (hint now reads "← Don't know / Know it →").
11. `AUTO_SPLIT_FEATURE.md` and `RATE_LIMIT_FIX.md` describe behaviour the code no longer has (50-word split, 1.5 s delay). `PDF_CONVERSION_GUIDE.md` and the root scripts hard-code `/Users/sujan/...` paths.
12. `test_api.py` in the repo root matches the test discovery pattern and makes live network calls at import.
13. `claude.md` (lowercase) asks for a `CLAUDE.md`; both names in one repo collide on macOS/Windows checkouts (see Important Decisions).
14. `config/settings.py` now falls back to `SECRET_KEY = 'this-is-for-testing-purpose'` when `DJANGO_SECRET_KEY` is unset (commit `95f904e`). That disables the startup guard: a deploy missing the variable runs with a public key instead of failing. Render sets the variable, so production is probably unaffected, but the guard is gone.
15. Commit `bb89564` renamed `.env.example` to `.env`, so a `.env` file is now tracked in git. Its contents were not inspected (reading credential files is blocked in this environment). If it holds a real key, that key must be rotated.

## Technical Debt

- Three fixed meaning columns (`meaning_1..3`); part of speech is baked into the meaning text as `(noun) …`.
- Empty `meaning_1 = ''` is the "needs lookup" marker; no index supports that filter.
- No DB constraint against duplicate words in a list; dedupe lives only in the parser.
- `Vocabulary.word_list` and `WordList.owner` are nullable although the app always sets them (owner is null only for the starter deck).
- `DictionaryAPI` prints to stdout instead of logging, does not URL-quote the word, and `fetch_meanings_batch` is unused.
- Inline styles throughout templates.
- Sample data files, `split_files/`, an empty `words` file and one-off scripts tracked in the repo root.
- Large uncommitted working tree (17 modified files, new CSS/JS/migration/commands) — the verified state above is the working tree, not `HEAD`.

## Project Tasks

Status legend: `[x]` implemented and verified, `[ ]` not done. "Partial" notes
describe what already exists so it is reused, not rebuilt.

### Phase 0 — Audit follow-ups (fix before new features)

- [x] FIX-001 — Commit the current working tree as the audited baseline
  - Completed: 2026-09-25 — committed by the owner (`5c0d780`); working tree clean.
- [x] FIX-002 — Validate ids; 404/400 instead of 500
  - Completed: 2026-09-25
  - Result: `id` path converter in `vocab/urls.py` (1–18 digits, no leading zero) replaces `<int:>` on every route, so oversized path ids 404. `parse_id()` in `vocab/views.py` validates `?list_id=`: `/api/cards/` returns 400 JSON, `/game/` treats it as a missing list. 5 tests in `InvalidIdTests`; suite 48/48.
- [ ] FIX-003 — Upgrade Django 4.2 → 5.2 LTS; rebuild the venv from `requirements.txt`; run tests and `check --deploy`
- [ ] FIX-004 — Retire or correct stale root docs; move `test_api.py` out of test discovery
- [ ] FIX-005 — Decide on `claude.md` vs `CLAUDE.md` (see Important Decisions)
- [ ] FIX-006 — Restore the fail-fast `SECRET_KEY` guard (Known Issue 14); needs the owner's agreement since the fallback was added on purpose
- [ ] FIX-007 — Owner checks the tracked `.env` (Known Issue 15): if it has real values, rotate them, `git rm --cached .env`, restore `.env.example`, add `.env` to `.gitignore`

### UI/UX refinement

- [x] UI-001 — Mobile-first UI/UX refinement, full-screen game — **COMPLETED**
  - Completed: 2026-09-25
  - Navigation: phones get a slim top bar (logo + Sign up or Log out) and a bottom tab bar (signed in: My lists / Play / Explore; guest: Home / Explore / Log in) with active states and safe-area padding. Desktop keeps top links from 768 px. Footer shows on desktop only.
  - Game: full-screen view with no site chrome (`100dvh`, safe areas, no page scroll). Top bar has exit, title, progress and a timer toggle; compact known/review/streak chips; the card fills the remaining space; answer buttons sit in the thumb zone and turn into one "Next card" button after answering. The in-card Next button and the top guest banner were removed (the guest note moved to the finish screen).
  - Swipe: Pointer Events with pointer capture, rAF-throttled `translate3d`, stamps that fade in with drag distance, flick detection, a fly-out in the answered direction, and the next card sliding up without re-rendering the stack. Cards underneath hide their word. The meaning side scrolls when long. Double taps on Next cannot skip a card; the timer auto-advance can no longer double-fire.
  - States: skeleton loading, clearer empty and error screens, a finish screen with accuracy %, Play again, and "Review missed words" (signed in, list decks).
  - Dashboard: stat tiles, "Play all" plus a timer button, list cards with a known-progress bar, Play/Timer/Review actions, and management (share code, visibility, edit, delete) moved into a "⋯" menu. Join and upload live under "Add a list"; upload is a disclosure that opens when there are no lists or on errors.
  - Home: "Start playing" goes straight into the first public list. The decorative preview is desktop only. Explore: search field with icon, cards with Play/Timer.
  - Style: one token set (colours checked for 4.5:1 contrast), 48 px minimum controls, 16 px inputs (no iOS zoom), inline SVG icon sprite, reduced-motion respected. Know = green, review = amber, brand red for primary actions.
  - Verified: 48/48 Django tests; headless Chromium at 320×640, 375×667, 390×844, 430×932, 768×1024 and 1280×800 checked for horizontal overflow on every page, no page scroll in the game, controls on screen, drag-swipe reveal + status POST, Next button, ←/Space keys, button answers, double-tap guard, timer mode, deck completion, menu close, and no console errors. `collectstatic` with the production storage succeeds.
  - No backend, API or URL changes.

### Phase 1 — Audit & Architecture

- [x] TASK-001 — Audit repository
  - Completed: 2026-09-25
  - Result: every app module, template, script, deploy file and migration read; tests, migration check and `check --deploy` run. Findings in Known Issues and `docs/`.
- [x] TASK-002 — Existing feature inventory
  - Completed: 2026-09-25 — `docs/ARCHITECTURE.md` → Feature Inventory.
- [x] TASK-003 — Architecture documentation
  - Completed: 2026-09-25 — `docs/ARCHITECTURE.md`.
- [x] TASK-004 — Database review
  - Completed: 2026-09-25 — `docs/ARCHITECTURE.md` → Database.
- [x] TASK-005 — Security audit
  - Completed: 2026-09-25 — `docs/SECURITY.md`. Findings recorded; none fixed yet.

### Phase 2 — Backend, Data Pipeline & Learning Engine

- [ ] TASK-006 — Vocabulary data architecture (pronunciation, part of speech, synonyms, difficulty, source)
  - Partial: word, up to 3 meanings, example, audio URL.
- [ ] TASK-007 — Import pipeline (TXT/CSV/XLSX/PDF)
  - Partial: TXT/CSV/TSV/XLSX parsing, cleaning, in-file dedupe. PDF only via offline scripts.
- [ ] TASK-008 — Automatic 50-word list splitting
  - Not in current code. Existed in `90be664`; check that version before rebuilding.
- [ ] TASK-009 — Background processing states and progress
  - Partial: pending/processing/completed/failed, total/processed counts, error message, resume after restart. Missing: started/completed timestamps, error count, cross-worker locking.
- [ ] TASK-010 — Learning state (NEW/LEARNING/REVIEW/KNOWN/MASTERED, seen/failed counts)
  - Partial: `is_known`, level, correct/wrong counts, last reviewed, next review.
- [ ] TASK-011 — Review algorithm isolated in a service
  - Partial: SM-2 lives in `WordProgress.apply_review`; not isolated, only two quality grades.
- [ ] TASK-012 — Learning sessions and summary
  - Partial: end-of-deck known/review counts in the browser only; nothing stored.
- [ ] TASK-013 — API layer review (methods, validation, consistent errors)

### Phase 3 — Learning Experience & Frontend

- [ ] TASK-014 — Learning interface (word, pronunciation, POS, meaning, example)
  - Partial: word, meanings, example, audio button.
- [ ] TASK-015 — Swipe left/right/up with visible legend and buttons
  - Partial: left/right swipe and buttons; no swipe up.
- [ ] TASK-016 — Desktop controls (← → ↑ Space)
  - Partial: ← → and Space/Enter for next; no ↑.
- [ ] TASK-017 — Dashboard (progress, remaining, review, sessions, daily activity, streak)
  - Partial: per-list totals/known/to-review, streak.
- [ ] TASK-018 — Progress visualization
- [ ] TASK-019 — Responsive design check (mobile, tablet, desktop)
- [ ] TASK-020 — Accessibility (live regions for cards, focus, contrast, labels)

### Phase 4 — Security, Testing, Performance & Production

- [ ] TASK-021 — Authentication security (rate limiting, password reset, enumeration)
- [ ] TASK-022 — Authorization tests on every endpoint
  - Partial: tests for private list access and foreign delete.
- [ ] TASK-023 — Upload security (xlsx decompression limits, processing time limits)
  - Partial: extension allow-list, 5 MB cap, word cap, in-memory parsing, nothing written to disk.
- [ ] TASK-024 — API security (rate limits, pagination, abuse of expensive endpoints)
- [ ] TASK-025 — Django production security review
  - Partial: settings are env-driven and `check --deploy` is clean; HSTS preload decision pending.
- [ ] TASK-026 — Dependency security (see FIX-003)
- [ ] TASK-027 — Database performance (dashboard N+1, card API size, indexes)
- [ ] TASK-028 — Test suite expansion
- [ ] TASK-029 — Performance testing (50 / 500 / 5,000 / 10,000+ words)
- [ ] TASK-030 — Deployment verification (PostgreSQL decision, health check endpoint, logs)
- [ ] TASK-031 — Documentation upkeep
  - Started 2026-09-25: `Plan.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/API.md`, `docs/DEPLOYMENT.md`.

## Completed Tasks

- 2026-09-25 — TASK-001 to TASK-005 (audit, inventory, architecture, database review, security audit).
- 2026-09-25 — FIX-001 (baseline committed), FIX-002 (id validation).
- 2026-09-25 — Production 500 fix (collectstatic at start, Render hostname in `ALLOWED_HOSTS`).
- 2026-09-25 — UI-001 mobile-first UI/UX refinement.

## In Progress

Nothing.

## Pending Tasks

Everything unchecked above, Phase 0 first.

## Next Recommended Task

**FIX-006 / FIX-007** (owner decisions, security), then **FIX-003** (Django 5.2 LTS).

FIX-006 and FIX-007 are small but need the owner: one reverts a deliberate
change, the other needs someone allowed to read the tracked env file. If they
are deferred, FIX-003 is next: Django 4.2 gets no more security releases.
After Phase 0, TASK-021/TASK-024 (rate limiting) come before Phase 2 features.

## Important Decisions

- 2026-09-25 — Project state lives in `Plan.md`, not a new `CLAUDE.md`. The repo already has a lowercase `claude.md` (the roadmap brief); adding `CLAUDE.md` beside it breaks checkouts on case-insensitive filesystems (the original developer works on macOS). Revisit in FIX-005: e.g. move the brief to `docs/ROADMAP.md` and then create `CLAUDE.md`.
- SQLite stays for now. The roadmap mentions PostgreSQL; switching is a TASK-030 decision, not something to do in passing.
- Background work stays an in-process thread unless evidence shows it fails (roadmap Rule 6: no unnecessary queues).
- The app does not use AI. Do not describe the review algorithm as AI.

## Things That Must Not Be Changed Without Review

- Existing migrations `0001`–`0009`, in particular the data migrations `0005` and `0009`.
- `WordList.share_code` format and uniqueness (codes are already shared with people).
- The upload file format described in `README.md`.
- `build.sh` / `start.sh` split: migrations run at start because the disk is only mounted at runtime.
- `DJANGO_DB_PATH` on the persistent disk and the SQLite WAL pragmas in `vocab/apps.py`.
- Security settings in the `if not DEBUG:` block of `config/settings.py`.
- Guest progress model (session codes + `localStorage`) and the signup carry-over.
