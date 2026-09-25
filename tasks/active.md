# Active tasks

Only tasks someone is working on right now. Template and rules: `CLAUDE.md`
and `.claude/agents/planner.md`.

---

### UI-001 — Refine VocabSwipe into a polished mobile-first learning app

- Status: **VERIFIED — awaiting owner sign-off** (not yet COMPLETED)
- Priority: current development task (set by the owner, 2026-09-25); no new feature work until it is closed
- Stages: planner → architect → developer → tester → security → human review → deployer → verification → completed
- Objective: make VocabSwipe feel like a modern mobile learning app, with the learning screen as an app-like full-screen mode, without changing core functionality.
- Background: the old UI was a desktop site shrunk to phones: a full top navbar, footer and page padding around the game, small touch targets, a hint that said "Swipe to reveal" although a swipe records the answer.
- Scope: templates, `static/css/app.css`, `static/js/game.js`, `static/js/dashboard.js`.
- Out of scope: backend, APIs, URLs, models, new features (swipe up, sessions, charts).
- Affected files: `templates/base.html`, `game.html`, `dashboard.html`, `home.html`, `explore.html`, `list_settings.html`, `registration/login.html`, `registration/signup.html`, `static/css/app.css`, `static/js/game.js`, `static/js/dashboard.js`.
- Dependencies: none.
- Risks: breaking the element ids the JS uses; iOS Safari viewport quirks that headless Chromium does not show.

**Acceptance criteria**

- [x] Learning screen fills the usable viewport (`100dvh`, safe areas) with no page scroll — `tests/ui/` at all sizes
- [x] Site navbar, tab bar and footer are hidden during learning; exit, progress and the timer toggle remain
- [x] Card is the visual focus; answer controls are in the thumb zone and on screen at every size
- [x] Swipe works, with directional feedback, a fly-out and a next-card transition; buttons and keys remain as alternatives
- [x] Mobile navigation takes little space, has active states and ≥ 44 px targets (bottom tab bar under 768 px)
- [x] Loading, empty, error and finished states are clear
- [x] No horizontal overflow at 320, 375, 390, 430 px, 768×1024, 1280×800
- [x] Authentication, upload, join, list management, progress saving and review mode still work — 48/48 Django tests, browser flow
- [x] Security review of the change — no findings (`docs/security.md` → Change reviews)
- [x] Deployed and live — commit `b2e7426` on `main`; 2026-09-25 `/explore/` returned 200 on both hostnames with the new markup
- [ ] **Real-device check** on iOS Safari and Android Chrome: safe areas, collapsing address bar, touch swipe feel, no rubber-band scroll in the game
- [ ] **Owner sign-off**

**Implementation summary** (details in `docs/test-reports/2026-09-25-ui-001.md`)

- Navigation: slim top bar plus bottom tab bar on phones (signed in: My lists / Play / Explore; guest: Home / Explore / Log in); desktop top links from 768 px; footer desktop-only.
- Game: full-screen mode, compact top bar, known/review/streak chips, answer buttons that become one "Next card" button after answering; Pointer Events swipe with rAF, flick detection, stamps, fly-out and stack promotion; hidden word on waiting cards; scrollable meaning side; double-tap and timer double-advance fixed; skeleton loading, finish screen with score and "Review missed words".
- Dashboard: stat tiles, Play all + timer, list cards with a known-progress bar, management in a "⋯" menu, "Add a list" with join and a collapsible upload.
- Style: one token set, contrast-checked colours, ≥ 48 px controls, 16 px inputs, SVG icon sprite, reduced motion respected.

**To close:** the owner checks the live site on a phone. If it is fine, move
this entry to `tasks/completed.md`. If not, list the problems here and set
the status back to `IMPLEMENTATION`.
