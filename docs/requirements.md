# Requirements

What VocabSwipe must do, as verified from the code and the owner's brief
(`docs/roadmap.md`). "Implemented" means present in the code and covered by
tests or a recorded check; "Stated" means the brief asks for it and the code
does not do it yet (the matching task is in `tasks/backlog.md`).

## Product purpose

Turn vocabulary files into an organized, trackable flash-card learning
experience. Primary users are students preparing for PTE and other English
exams, mostly on phones. The architecture stays generic enough for any word
collection.

## Functional requirements

### Accounts

| Requirement | Status |
| --- | --- |
| Sign up with username and password; log in; log out (POST) | Implemented |
| Play public lists and code-unlocked lists without an account | Implemented |
| Guest progress kept in the browser; unlocked lists carried over on signup | Implemented |
| Password reset | Stated (TASK-021: "password reset security"); not implemented, no email is configured |

### Word lists

| Requirement | Status |
| --- | --- |
| Upload `.txt`, `.csv`, `.tsv`, `.xlsx`/`.xlsm`; one word per line, optional meanings separated by `;` | Implemented |
| Skip a header row, keep quoted commas, collapse repeated words, keep up to three meanings | Implemented |
| Bare words get meanings, an example and audio from dictionaryapi.dev in the background, with visible progress; interrupted lookups resume | Implemented |
| Each list has a unique six-character share code; join by code; make public or private; edit name/description; delete; leave a joined list | Implemented |
| Explore public lists with search | Implemented |
| A public starter deck on a fresh install | Implemented (migration `0009`) |
| PDF import in the app | Stated (TASK-007); offline script only |
| Automatic split into 50-word lists | Stated (TASK-008) |
| Pronunciation text, part of speech, synonyms, antonyms, difficulty, source per word | Stated (TASK-006) |

### Learning

| Requirement | Status |
| --- | --- |
| One card at a time: word first, meaning and example after answering | Implemented |
| Answer by swipe (right = know, left = review), by buttons, or by ← / → keys; Space/Enter for next | Implemented |
| Classic mode and timer mode (3–120 s per card; timeout counts as review) | Implemented |
| Signed-in answers saved per user and word, scheduled with SM-2 | Implemented |
| Review mode: unknown words plus known words that are due | Implemented |
| Daily streak and total reviews | Implemented |
| End-of-deck summary (score, known, to review, replay, review missed) | Implemented (browser only) |
| Staged learning states (NEW … MASTERED), stored sessions, session history | Stated (TASK-010, TASK-012) |
| Swipe up / ↑ action | Stated (TASK-015, TASK-016); meaning not defined yet |

## Non-functional requirements

| Requirement | Status |
| --- | --- |
| Mobile first; works at 320, 375, 390, 430 px, tablet and desktop | Implemented, checked with `tests/ui/` (UI-001) |
| Learning screen is a full-viewport app mode with thumb-reach controls | Implemented (UI-001) |
| Accessible: labels, keyboard control, visible focus, 4.5:1 text contrast, reduced motion | Partly implemented (UI-001); full review is TASK-020 |
| No third-party CSS, fonts or scripts at runtime | Implemented (test `test_pages_reference_the_local_stylesheet_not_a_cdn`) |
| Secrets from the environment; secure cookies, HTTPS and HSTS in production | Implemented, with open findings S15/S16 in `docs/security.md` |
| Users can only reach their own or shared/public lists and only change their own | Implemented; broader tests are TASK-022 |
| Bad input returns 400/404, never 500 | Implemented for ids (FIX-002); API review is TASK-013 |
| Rate limiting on login, codes, uploads and answers | Stated (TASK-021, TASK-024) |
| Uploads bounded: 5 MB, 20,000 words, parsed in memory, never stored on disk | Implemented; xlsx expansion limits are TASK-023 |
| Large imports do not block requests | Partly: parsing is in the request, lookups are in the background (TASK-009) |
| Supported framework version | Not met: Django 4.2 is out of support (FIX-003) |

## User flows

1. **Guest, first visit:** Home → "Start playing" → first public list in the game → finish screen → sign up to keep progress.
2. **Guest with a code:** Home → enter code → game for that list (unlocked for the session).
3. **New user:** Sign up → dashboard → Add a list → upload a file → list card (lookup progress if needed) → Play.
4. **Returning user:** Log in → dashboard stats → Play all, or a list's Play / Timer / Review → answers saved → streak updated.
5. **Sharing:** list "⋯" menu → copy share code or make public → friend joins by code or finds it in Explore.

## Constraints

- One Django project with templates; no frontend framework or build step.
- SQLite on a single Render disk; Gunicorn with several worker processes.
- dictionaryapi.dev is free and rate-limited; lookups pause between words.
- Production deploys from `main`; changes to production need owner approval.

## Acceptance criteria

Acceptance criteria are written per task in `tasks/active.md` and
`tasks/backlog.md`, and checked in `docs/test-reports/`.
