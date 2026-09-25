# Architecture

Describes the code as it is on 2026-09-25 (working tree, including
uncommitted changes). Planned work is in `Plan.md`, not here.

## Request flow

```
Browser (templates + game.js / dashboard.js, no build step)
  │  HTML pages, form POSTs, fetch() JSON calls with CSRF header
  ▼
Gunicorn (start.sh, 3 workers)
  ▼
Django middleware: Security → WhiteNoise → Session → Common → CSRF → Auth → Messages → XFrame
  ▼
config/urls.py → vocab/urls.py → vocab/views.py (function views)
  │   access helpers: accessible_lists(), can_play(), playable_lists()
  │   forms:          vocab/forms.py
  │   parsing:        vocab/utils/parsing.py
  │   background:     vocab/tasks.py ──► vocab/utils/dictionary_api.py ──► dictionaryapi.dev
  ▼
Django ORM → SQLite (WAL, timeout 20 s; file at DJANGO_DB_PATH)
```

There is no separate service layer: business logic sits in views, in model
methods (`WordProgress.apply_review`, `UserStats.update_streak`) and in
`tasks.py`.

## Vocabulary pipeline

```
Vocabulary source      Upload form on /dashboard/ (dashboard_view, action=upload)
                       Offline: extract_pdf_vocab.py, convert_pdf_to_vocab.py (PyPDF2, not installed by requirements.txt)
  ▼
Validation (file)      UploadFileForm.clean_file: extension allow-list (.txt .csv .tsv .xlsx .xlsm), 5 MB cap
  ▼
Extraction             parsing._parse_text (csv.reader, utf-8-sig/utf-8/latin-1) or parsing._parse_sheet (openpyxl read_only, active sheet)
  ▼
Cleaning               parsing._clean (whitespace collapse), _split_meanings (';' or '|'), header-row skip, 'nan'/'none' rows dropped
                       Offline: clean_vocab.py
  ▼
Validation (rows)      _row_to_entry: word ≤ 255 chars, ≤ 3 meanings; MAX_WORDS = 20,000 (silent truncation)
  ▼
Deduplication          parse_vocabulary_file: case-insensitive, first spelling wins, within one file only
  ▼
Splitting              NOT IN THE APP. One upload = one WordList. Removed after commit 90be664.
                       Offline: split_vocab_file.py (500 words per file)
  ▼
Storage                WordList.objects.create + Vocabulary.objects.bulk_create (in the request)
  ▼
Processing             Only if some word has no meaning: tasks.start_background_processing
                       → daemon thread → fetch_meanings_for_list (0.5 s pause per word, 3 retries on 429)
                       → progress in WordList.words_processed, status pending → processing → completed/failed
                       Recovery: resume_lookups at boot (processing → pending), resume_pending_lookups on dashboard load
  ▼
Vocabulary lists       Dashboard cards, share code, public toggle, Explore
  ▼
Learning system        /game/ + game.js → GET /api/cards/ → POST /api/cards/<id>/status/ → WordProgress.apply_review (SM-2) + UserStats.update_streak
```

## Learning flow

1. `game_view` checks access (`can_play`) and renders `game.html` with mode, seconds, list, review flag.
2. `game.js` fetches `/api/cards/` (all playable cards, random order) and renders a three-card stack. The game page hides the site header, tab bar and footer and fills the viewport.
3. Answer by swipe (Pointer Events: 96 px drag or a quick flick), the bottom buttons, or ← / →. Timer mode counts an expired card as "review".
4. The card flips to show meanings and example; the bottom "Next card" button, Space or Enter sends it off and the next card moves up.
5. Signed in: POST status → SM-2 update and streak. Guest: card IDs stored in `localStorage` under `vocabswipe:guest:<list|all>`.
6. End of deck: known / to-review counts shown in the browser. Nothing is stored about the session.

## Access model

| Who | Can play |
| --- | --- |
| Anyone | Public lists |
| Guest with a code | Lists whose code is in `session['unlocked_codes']` |
| Signed-in user | Own lists, joined lists (`JoinedList`), public lists, session-unlocked lists |

Owner-only actions (settings, visibility, delete) filter by `owner=request.user`.
Leaving a list deletes only the caller's `JoinedList` row.

## Database

### Models

| Model | Key fields | Relations / constraints |
| --- | --- | --- |
| `WordList` | name, description (280), file_name, share_code (unique, 6 of 32 chars), is_public (indexed), created_at, processing_status, total_words, words_processed, error_message | owner → User, CASCADE, nullable (null only for the starter deck) |
| `Vocabulary` | word (255), meaning_1 (required, `''` = needs lookup), meaning_2, meaning_3, example_sentence, audio_url, created_at | word_list → WordList, CASCADE, nullable |
| `WordProgress` | is_known, level, correct_count, wrong_count, last_reviewed, next_review_date, interval, easiness_factor, repetition_count | user, vocabulary (both CASCADE); unique (user, vocabulary); index (user, is_known) |
| `JoinedList` | joined_at | user, word_list (CASCADE); unique (user, word_list) |
| `UserStats` | current_streak, longest_streak, last_review_date, total_reviews | one-to-one user |

Migrations: `0001`–`0003` early schema (generated by Django 6.0.1, although the
project now pins 4.2), `0004`–`0006` auth, sharing and the move of `is_known`
into per-user progress (`0005` is a data migration), `0007`–`0008` public
lists, processing fields, SM-2 fields, `UserStats`, `0009` starter deck (data).
`makemigrations --check` reports no drift.

### Review findings

- **Missing constraints:** no unique (word_list, lower(word)); duplicates across uploads or via admin are possible.
- **Nullable FKs the app never leaves null:** `Vocabulary.word_list`. `WordList.owner` is null by design for the starter deck; templates handle it.
- **Sentinel value:** `meaning_1 = ''` marks "needs lookup"; failed lookups write placeholder text into `meaning_1`, so real and missing definitions mix.
- **Fixed columns:** three meaning columns; part of speech embedded in text. Blocks TASK-006 (POS, synonyms, pronunciation).
- **Indexes:** `Vocabulary(word_list, meaning_1)` would serve the lookup query; `WordProgress(user, next_review_date)` would serve review mode. Not a measured problem yet.
- **Timestamps:** `Vocabulary` and `WordList` have `created_at` only; no `updated_at`. `WordProgress` has no created time. Processing has no started/completed times.
- **Counters:** `total_words` / `words_processed` duplicate what `words.count()` can compute; they are only for lookup progress.
- **Scalability:** `/api/cards/` loads the whole deck; dashboard does one query per list and loads all known IDs into a Python set.
- **Unsafe fields:** none storing secrets. `audio_url` comes from the third-party API and is only checked for a scheme prefix.

## Feature inventory

### Working

- Sign up (username + password), log in, log out (POST).
- Upload TXT/CSV/TSV/XLSX(M) with the parsing rules above.
- Background meaning lookup with progress bar, resume after restart, `fetch_meanings` / `resume_lookups` commands.
- Classic and timer game modes; swipe, buttons, ← / → keys, Space/Enter for next; audio button.
- SM-2 scheduling, review mode, daily streak.
- Share codes, join by code, public/private toggle, list settings, delete, leave.
- Explore with search; home page with top six public lists.
- Guest play with browser-side progress; signup carries unlocked lists over.
- Starter deck on fresh installs.
- Admin for all models.

### Partially implemented

- Background processing: no timestamps, no error count, no cross-worker lock.
- Learning state: binary known / unknown instead of staged states.
- Review: SM-2 embedded in the model with two grades only.
- Dashboard: totals and streak, no activity history or sessions.
- Keyboard controls: no ↑ action.
- Import: PDF only through offline scripts with hard-coded paths.

### Broken

- Non-numeric or oversized `list_id` → HTTP 500 on `/game/` and `/api/cards/`.
- "Review N" count on the dashboard disagrees with what review mode serves.

### Missing

- Automatic 50-word list splitting.
- Learning sessions (start, end, accuracy, summary stored).
- Pronunciation text, part of speech field, synonyms, antonyms, difficulty, source.
- Swipe up gesture.
- Password reset, email.
- Rate limiting of any kind.
- Progress charts.
- Custom 404/500 pages; a dedicated health-check endpoint.

### Technical debt, security and performance

See `Plan.md` → Known Issues / Technical Debt and `docs/SECURITY.md`.

## Where things live

| Concern | File |
| --- | --- |
| Settings, security flags, logging | `config/settings.py` |
| SQLite pragmas | `vocab/apps.py` |
| Models, SM-2, streak | `vocab/models.py` |
| Views, access helpers, JSON API | `vocab/views.py` |
| Forms, upload limits | `vocab/forms.py` |
| Parsing | `vocab/utils/parsing.py` |
| Dictionary client | `vocab/utils/dictionary_api.py` |
| Background lookup | `vocab/tasks.py` |
| Management commands | `vocab/management/commands/` |
| Card game UI | `templates/game.html`, `static/js/game.js` |
| Dashboard UI | `templates/dashboard.html`, `static/js/dashboard.js` |
| Styles | `static/css/app.css` |
| Tests | `vocab/tests.py` |
| Deployment | `build.sh`, `start.sh`, `render.yaml`, `Procfile`, `.env.example` |
