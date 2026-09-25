# Backlog

Pending work. Priority uses the project's own ordering: **Phase 0** (audit
fixes, before new features) then Phases 1–4 of `docs/roadmap.md`. Within a
phase, top to bottom. Nothing here starts while UI-001 is open in
`tasks/active.md`.

"Partial" notes say what already exists, so it is reused instead of rebuilt.

## Existing tasks

### Phase 0 — audit follow-ups

#### FIX-006 — Restore the fail-fast `SECRET_KEY` guard
- Priority: Phase 0 · Status: BACKLOG · Needs owner decision (the fallback was added on purpose in `95f904e`)
- Description: `config/settings.py` falls back to `'this-is-for-testing-purpose'`, so the "refuse to start without a key when `DEBUG` is off" check never fires (security finding S15).
- Dependencies: none.
- Acceptance criteria:
  - [ ] With `DJANGO_DEBUG=0` and no `DJANGO_SECRET_KEY`, startup fails with the existing message.
  - [ ] `DJANGO_DEBUG=1` still works without a key; `manage.py test` still runs.
  - [ ] Render still boots (it sets the key).

#### FIX-007 — Stop tracking `.env`
- Priority: Phase 0 · Status: BACKLOG · Owner action (agents may not read the file)
- Description: `bb89564` renamed `.env.example` to `.env`, so an env file is in git (S16).
- Acceptance criteria:
  - [ ] Owner confirms whether it held real values; if so they are rotated on Render.
  - [ ] `.env` removed from the index (`git rm --cached .env`) and listed in `.gitignore`.
  - [ ] A placeholder-only `.env.example` is restored.

#### FIX-003 — Upgrade Django 4.2 → 5.2 LTS
- Priority: Phase 0 · Status: BACKLOG · Stages: planner → architect → developer → tester → security → approval → deployer
- Description: 4.2 is out of support (S1). Check release notes for 5.0–5.2 against the code (settings, `LogoutView`, `STORAGES`, test client), pin compatible versions of the other packages, rebuild the virtualenv from `requirements.txt` (the local one has 4.2.0).
- Acceptance criteria:
  - [ ] `requirements.txt` pins Django 5.2.x; tests, migration check, `check --deploy` and production `collectstatic` pass.
  - [ ] Viewport check passes.
  - [ ] Deployed and verified on Render.

### Phase 2 — backend, data pipeline, learning engine

#### TASK-006 — Vocabulary data model
- Status: BACKLOG · Partial: word, up to 3 meanings, example, audio URL.
- Description: pronunciation, part of speech, synonyms, antonyms, difficulty, source, without breaking existing rows.
- Dependencies: FIX-003 preferred first.
- Acceptance criteria: new fields migrated with existing data intact; parser and dictionary client fill what they can; cards show them without clutter.

#### TASK-007 — Import pipeline, including PDF
- Status: BACKLOG · Partial: TXT/CSV/TSV/XLSX parsing, cleaning, in-file dedupe; PDF only in `scripts/convert_pdf_to_vocab.py`.
- Acceptance criteria: PDF upload goes through the same validation and limits; malformed and empty files report clear errors.

#### TASK-008 — Automatic 50-word list splitting
- Status: BACKLOG · Existed in commit `90be664` and was removed; read that version first.
- Acceptance criteria: 3,153 words become 63 lists of 50 and one of 3, each playable on its own; no whole-file load beyond the parser.

#### TASK-009 — Background processing states
- Status: BACKLOG · Partial: pending/processing/completed/failed, counts, error message, resume after restart.
- Missing: started/completed timestamps, error count, a lock that works across Gunicorn workers.

#### TASK-010 — Learning states
- Status: BACKLOG · Partial: `is_known`, level, correct/wrong counts, last reviewed, next review.
- Description: NEW / LEARNING / REVIEW / KNOWN / MASTERED and seen/failed counters; known words are never deleted.

#### TASK-011 — Review algorithm as a replaceable service
- Status: BACKLOG · Partial: SM-2 inside `WordProgress.apply_review`, two grades.

#### TASK-012 — Stored learning sessions and summary
- Status: BACKLOG · Partial: end-of-deck summary in the browser only (UI-001).

#### TASK-013 — API review
- Status: BACKLOG · Partial: ids validated (FIX-002).
- Description: consistent error format, method checks, validation on every endpoint (`docs/api.md` → Known gaps).

### Phase 3 — learning experience and frontend

UI-001 covered much of TASK-014, TASK-017, TASK-019 and TASK-020. Re-plan
these against the current UI before starting.

- **TASK-014 — Learning interface fields** · BACKLOG · Needs TASK-006 for pronunciation and part of speech.
- **TASK-015 — Swipe up** · BACKLOG · Left/right and buttons exist; the meaning of "up" must be defined by the owner.
- **TASK-016 — ↑ key** · BACKLOG · Same decision as TASK-015; ←, →, Space, Enter exist.
- **TASK-017 — Dashboard metrics** · BACKLOG · Stats, per-list progress and streak exist; sessions and daily activity need TASK-012.
- **TASK-018 — Progress visualization** · BACKLOG · Per-list progress bars exist.
- **TASK-019 — Responsive check** · BACKLOG · Done for UI-001 in headless Chromium; real-device pass still open.
- **TASK-020 — Accessibility review** · BACKLOG · Labels, focus, contrast, live regions added in UI-001; needs a screen-reader pass.

### Phase 4 — security, testing, performance, production

- **TASK-021 — Authentication security** · BACKLOG · Rate-limit login/signup/admin (S2), password reset without account enumeration (S11, S14).
- **TASK-022 — Authorization tests on every endpoint** · BACKLOG · Partial tests exist.
- **TASK-023 — Upload limits** · BACKLOG · Bound xlsx expansion and parse time (S6); tell the user when words are dropped at 20,000.
- **TASK-024 — API abuse limits** · BACKLOG · Rate-limit share-code guesses (S3), uploads (S8) and answers (S7); cap or paginate `/api/cards/` (S5).
- **TASK-025 — Production settings review** · BACKLOG · Decide on HSTS preload (S12); CSP (S17).
- **TASK-026 — Dependency review** · BACKLOG · See FIX-003; add `pip-audit` if the owner agrees.
- **TASK-027 — Database performance** · BACKLOG · Dashboard N+1, `/api/lists/` counts, indexes for lookups and review mode.
- **TASK-028 — Test suite expansion** · BACKLOG
- **TASK-029 — Performance test with 50 / 500 / 5,000 / 10,000+ words** · BACKLOG
- **TASK-030 — Deployment** · BACKLOG · PostgreSQL decision, a dedicated health endpoint, backups (`docs/deployment.md`).
- **TASK-031 — Documentation upkeep** · ongoing.

## Newly identified technical debt

Found during the audit and the workflow setup; not in the roadmap.

- **DEBT-001** — Words with no dictionary entry store the placeholder `No definition found for "…"` in `meaning_1`, indistinguishable from real data.
- **DEBT-002** — Dashboard "Review N" counts unknown words, but review mode also serves due known words.
- **DEBT-003** — The lookup thread's duplicate guard is per process; two workers can process the same list.
- **DEBT-004** — `DictionaryAPI` prints instead of logging, does not URL-quote the word (S9), accepts any audio URL scheme (S10); `fetch_meanings_batch` is unused.
- **DEBT-005** — No DB constraint against duplicate words in a list; nullable `Vocabulary.word_list`.
- **DEBT-006** — Inline `style` attributes and one inline `onsubmit` in templates (blocks a strict CSP, S17).

## Improvement opportunities

Ideas that came up; each needs the owner's go-ahead before it becomes a task.

- **IDEA-001** — Seed `tests/ui/` data from a management command instead of `manage.py shell < file`.
- **IDEA-002** — A GitHub Actions workflow that runs `manage.py test` on push (there is no CI today).
- **IDEA-003** — Error tracking or uptime alerts for production (none today).
