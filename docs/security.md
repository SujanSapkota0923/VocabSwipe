# Security

Owned by the `security` agent. Audit of the working tree on 2026-09-25. Fixed findings are marked. Severity is a judgement for this app's exposure (public site,
user accounts, no payment or personal data beyond usernames).

## What is in place

- **Secrets:** `DJANGO_SECRET_KEY` from the environment. The fail-fast guard for a missing key is currently bypassed (S15). No secrets found in tracked source files; a tracked `.env` is unverified (S16). `db.sqlite3` is git-ignored and not tracked.
- **Debug:** off unless `DJANGO_DEBUG` is set.
- **Hosts / CSRF:** `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` from the environment, defaulting to the production domain.
- **HTTPS (DEBUG off):** `SECURE_PROXY_SSL_HEADER`, optional `SECURE_SSL_REDIRECT`, secure session and CSRF cookies, HSTS 1 year with subdomains and preload, `nosniff`, `X_FRAME_OPTIONS = 'DENY'`. `manage.py check --deploy` passes with no warnings.
- **CSRF:** middleware on; no `csrf_exempt`. `game.js` sends `X-CSRFToken` on the status POST. Logout is POST.
- **Passwords:** Django defaults (PBKDF2) with all four standard validators.
- **Authorization:** owner-only views filter by `owner=request.user` (no fetch-then-check). Card status and list progress call `can_play()` before touching data. Unauthorized list reads return 404, not 403, so list existence is not confirmed.
- **Uploads:** extension allow-list, 5 MB cap, parsed in memory and never written to disk, so there is no stored-file, path-traversal or execution surface. Filenames are only stored as text and rendered escaped.
- **Output encoding:** Django autoescape everywhere; `game.js` builds card content with `textContent`. The only `innerHTML` uses are static strings. The one `|safe` renders Django's own password help text.
- **SQL:** ORM only; no raw SQL apart from the SQLite `PRAGMA` statements.
- **Errors:** upload parse failures show a generic message and log the exception. JSON endpoints return short messages, no stack traces.

## Findings

| # | Severity | Finding | Where |
| --- | --- | --- | --- |
| S1 | High | Django 4.2 left extended support in April 2026; no further security fixes. The local environment also runs 4.2.0, not the pinned 4.2.30. | `requirements.txt` |
| S2 | Medium | No rate limiting on login, signup or admin login: password guessing is unthrottled. | `vocab/urls.py`, `/admin/` |
| S3 | Medium | Share codes can be brute-forced: `/game/?code=` and both join forms accept unlimited guesses. Space is 32⁶ ≈ 1.07 × 10⁹, so this is slow but unbounded, and a hit unlocks a private list. | `game_view`, `home_view`, `dashboard_view` |
| S4 | Fixed | **Fixed 2026-09-25 (FIX-002).** Invalid `list_id` raises `ValueError` / `OverflowError` → 500. Not an information leak with `DEBUG` off, but it is an unhandled input path and noise in the error log. | `game_view`, `playable_lists` |
| S5 | Medium | `/api/cards/` has no pagination or limit and uses `ORDER BY RANDOM()`; a signed-in user with many large lists can make every request expensive. | `card_list_api` |
| S6 | Medium | XLSX is a zip: a 5 MB upload can expand far beyond that when openpyxl reads shared strings. Parsing runs synchronously inside the request with no time or memory bound. | `parsing._parse_sheet` |
| S7 | Low | Card status POSTs are unthrottled; any client can inflate `total_reviews` and streak for its own account. Affects only the caller's data. | `update_card_status_api` |
| S8 | Low | Upload endpoint unthrottled; each bare-word upload starts a thread making up to 20,000 outbound requests to dictionaryapi.dev. | `dashboard_view`, `tasks.py` |
| S9 | Low | Dictionary client interpolates the word into the URL path without quoting. The host is fixed, so this is not SSRF, but characters like `/` or `?` change the request. | `dictionary_api.py` |
| S10 | Low | `audio_url` from the third-party API is stored and played with only a scheme-prefix check. `new Audio(url)` does not execute script, so impact is limited to loading arbitrary media URLs. | `dictionary_api.py`, `game.js` |
| S11 | Low | No password reset. Not a vulnerability, but a user who forgets a password loses their progress; any future reset flow must avoid account enumeration. | — |
| S12 | Info | `SECURE_HSTS_PRELOAD = True` is hard-coded. Submitting the domain to the preload list is hard to undo; keep it only if that is intended. | `config/settings.py` |
| S13 | Info | Admin is at the default `/admin/`. Fine with strong passwords and S2 fixed. | `config/urls.py` |
| S15 | High | `SECRET_KEY` falls back to a hard-coded public string when `DJANGO_SECRET_KEY` is unset (commit `95f904e`), bypassing the fail-fast guard. Anyone who knows the string can forge sessions on a deploy that forgot the variable. | `config/settings.py` |
| S16 | Unverified | `.env` tracked in git since commit `bb89564` (renamed from `.env.example`). Contents not inspected. If it holds a real key, rotate it and remove the file from the index; history keeps the old value. | `.env` |
| S17 | Info | No Content-Security-Policy header. Templates use one inline `onsubmit` handler (delete confirmation) and inline `style` attributes, so a future CSP needs `'unsafe-inline'` or those moved into `static/`. | `templates/dashboard.html` |
| S14 | Info | Signup reveals whether a username exists (standard Django behaviour). Acceptable for a username-only app; note it for TASK-021. | `SignupForm` |

## Change reviews

| Date | Change | Result |
| --- | --- | --- |
| 2026-09-25 | FIX-002 id validation | Removes a 500 path (S4 fixed). No new surface. |
| 2026-09-25 | FIX-008 deployment fix (`collectstatic` at start, `RENDER_EXTERNAL_HOSTNAME` appended to `ALLOWED_HOSTS`) | No findings. The appended host comes from Render's own environment, not from requests. |
| 2026-09-25 | Debug-only `ALLOWED_HOSTS = ['*']` | No findings for production: the wildcard only applies when `DJANGO_DEBUG` is on. Never run a public server with debug on. |
| 2026-09-25 | UI-001 (templates, CSS, `game.js`, `dashboard.js`; commit `b2e7426`) | No findings. No new endpoints, forms, `|safe`, or HTML built from data: card text is set with `textContent`/`setAttribute`, template values are autoescaped, every POST form keeps `{% csrf_token %}`, the status POST still sends `X-CSRFToken`, and no new third-party resources are loaded. S17 noted. |

## Not applicable today

- **CORS:** no cross-origin API consumers; no CORS headers are set, which is correct.
- **File storage / media:** `MEDIA_ROOT` is configured but nothing is written there.
- **API tokens:** the API uses session auth only.

## Recommended order

1. S15, S16 (FIX-006, FIX-007) — secret handling.
2. S1 (FIX-003) — dependency upgrade.
3. S2, S3, S7, S8 — one small rate-limit mechanism (Django cache based) applied to login, code lookups, uploads and status POSTs.
4. S5 — cap or paginate the card API.
5. S6 — cap rows/cells read from sheets and consider moving parsing out of the request.
6. S9, S10 — quote the word; accept only `https:` audio URLs.
