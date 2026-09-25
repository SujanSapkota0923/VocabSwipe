# Completed tasks

Newest first. A task is here only after its acceptance criteria were verified.

---

### WF-001 — Multi-agent development workflow
- Completed: 2026-09-25
- Summary: `CLAUDE.md` control document; agents `planner`, `architect`, `developer`, `tester`, `security`, `deployer` in `.claude/agents/`; `.claude/skills/README.md`; `tasks/` backlog/active/completed; docs renamed to lowercase and extended (`requirements.md` new, Mermaid overview and decisions in `architecture.md`, local/rollback/backup/monitoring in `deployment.md`, change reviews in `security.md`); `tests/ui/` viewport check and seed script; test report for UI-001. `Plan.md` retired: its content now lives in `CLAUDE.md` and `tasks/`.
- Files: `CLAUDE.md`, `.claude/`, `tasks/`, `docs/*`, `tests/ui/`, `README.md`, `.gitignore`; removed `Plan.md`.
- Tests: 48/48 Django tests; `tests/ui/viewport_check.js` run from the repository against a freshly seeded DB: `NO PROBLEMS`.
- Security review: not required (documentation and tooling only).
- Deployment: no application change.
- Known limitations: no Docker, CI or `backend/`/`frontend/` split by design (see `docs/architecture.md` → Decisions).

### FIX-004 / FIX-005 — Repository cleanup
- Completed: 2026-09-25 (commit `29cddd3`)
- Summary: removed stale notes, one-off scripts with hard-coded paths, duplicate word files, `split_files/`, `test_api.py`, empty and unrelated files; word files moved to `wordlists/`, helpers to `scripts/`, the brief from root `claude.md` to `docs/roadmap.md`.
- Tests: 48/48; scripts compile.
- Security review: not required. Deployment: no application change.

### FIX-008 — Production 500 and 400
- Completed: 2026-09-25 (commit `824b92d`)
- Summary: every page returned 500 (`Missing staticfiles manifest entry for 'css/app.css'`) because the build had not collected static files; `start.sh` now runs `collectstatic`. The `onrender.com` host returned 400; `RENDER_EXTERNAL_HOSTNAME` is now appended to `ALLOWED_HOSTS`.
- Files: `start.sh`, `config/settings.py`, `docs/deployment.md`.
- Tests: reproduced locally with `DEBUG=0` (500 without the manifest, 200 with it); 48/48; `check --deploy` clean.
- Security review: no findings (`docs/security.md` → Change reviews).
- Deployment: live; 200 on both hostnames on 2026-09-25.

### DEV-001 — Any host in local debug
- Completed: 2026-09-25 (commit `9070762`)
- Summary: with `DJANGO_DEBUG=1` and no `DJANGO_ALLOWED_HOSTS`, `ALLOWED_HOSTS = ['*']` so phones on the LAN can reach `runserver 0.0.0.0:8000`. Production defaults unchanged.
- Tests: settings printed in both modes; 48/48.
- Security review: no production impact (`docs/security.md` → Change reviews).

### FIX-002 — Invalid ids return 404/400, not 500
- Completed: 2026-09-25 (commit `dd8ea0c`)
- Summary: `id` path converter (1–18 digits) on every route; `parse_id()` for `?list_id=`; `/api/cards/` returns 400 JSON, `/game/` treats a bad id as a missing list.
- Files: `vocab/urls.py`, `vocab/views.py`, `vocab/tests.py` (`InvalidIdTests`, 5 tests).
- Tests: 48/48; endpoints re-probed.
- Security review: removes a 500 path (S4).

### FIX-001 — Audited baseline committed
- Completed: 2026-09-25 — committed by the owner (`5c0d780`).

### TASK-001 to TASK-005 — Audit
- Completed: 2026-09-25
- Summary: repository audit, feature inventory, architecture, database review and security audit, recorded in `docs/architecture.md` and `docs/security.md`.
- Tests: suite, migration check and `check --deploy` run.
