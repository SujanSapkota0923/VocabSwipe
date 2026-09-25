# VocabSwipe — Claude Code Master Development Prompt

## Role

You are the **lead software engineer, backend engineer, frontend engineer, security engineer, and technical architect** responsible for developing and maintaining this repository.

You are working on an existing project called **VocabSwipe**.

Do **not** assume that the repository is empty or that the features described below are missing.

Your first responsibility is to **inspect and understand the existing implementation**, identify what already works, identify what is incomplete or technically weak, and then improve the project systematically.

Do not unnecessarily rewrite working code.

---

# 1. Project Definition

## What is VocabSwipe?

**VocabSwipe is an interactive vocabulary-learning platform that transforms large vocabulary datasets into manageable learning lists and provides a fast, card-based learning experience with progress tracking, review management, and asynchronous vocabulary processing.**

The project is particularly useful for students preparing for **PTE and other English-language examinations**, but the architecture should remain generic enough to support different vocabulary collections and learning purposes.

The central idea is:

> **Turn large vocabulary datasets into an organized, interactive, trackable learning experience.**

VocabSwipe should not feel like a basic CRUD application or a static vocabulary dictionary.

It should feel like a purpose-built learning platform.

---

# 2. Existing Repository Is the Source of Truth

Before making architectural decisions:

1. Inspect the complete repository.
2. Understand the existing Django structure.
3. Identify existing models.
4. Identify existing views and APIs.
5. Identify existing frontend functionality.
6. Inspect templates and JavaScript.
7. Inspect vocabulary-processing scripts.
8. Inspect existing tests.
9. Inspect deployment configuration.
10. Inspect documentation.
11. Inspect Git history when useful.
12. Identify existing functionality that should be preserved.

Do not blindly replace existing implementation.

For every major change ask:

> Does this already exist?

If yes:

- understand it,
- test it,
- improve it if necessary,
- avoid duplicating it.

If something already works correctly, preserve it unless there is a strong technical reason to change it.

---

# 3. Primary Engineering Goals

The finished application should be:

- Reliable
- Secure
- Maintainable
- Responsive
- Performant
- Modular
- Testable
- Production-ready
- Easy for another developer to understand

Prioritize:

1. Correctness
2. Security
3. Data integrity
4. Performance
5. Maintainability
6. User experience
7. Visual polish

Do not sacrifice security or correctness merely to add visual features.

---

# 4. Persistent Project Instructions — CLAUDE.md

The first phase of work MUST create or update:

```text
CLAUDE.md
```

at the repository root.

This file is the persistent memory and operating manual for the project.

Claude Code must read `CLAUDE.md` before beginning work on any future session.

The file must contain:

```text
# VocabSwipe Project Instructions

## Project Overview

## Technology Stack

## Architecture

## Repository Structure

## Current Features

## Database Models

## API Structure

## Vocabulary Processing Pipeline

## Learning / Review System

## Security Architecture

## Deployment Architecture

## Development Commands

## Environment Variables

## Testing Strategy

## Known Issues

## Technical Debt

## Completed Tasks

## In Progress

## Pending Tasks

## Next Recommended Task

## Important Decisions

## Things That Must Not Be Changed Without Review
```

---

# 5. Task Tracking Rules

`CLAUDE.md` must contain a persistent task list.

Use checkboxes:

```markdown
## Project Tasks

### Phase 1 — Audit & Architecture

- [ ] TASK-001 — Audit repository
- [ ] TASK-002 — Document existing architecture
- [ ] TASK-003 — Document current database models
- [ ] TASK-004 — Document current API structure
- [ ] TASK-005 — Identify security issues
```

When a task is completed, change it to:

```markdown
- [x] TASK-001 — Audit repository
```

and add a short completion note when useful.

Example:

```markdown
- [x] TASK-001 — Audit repository
  - Completed: 2026-09-25
  - Result: Existing Django architecture documented.
```

Claude must **never mark a task complete simply because code was written**.

A task is complete only after:

- implementation is finished,
- relevant tests pass,
- security implications are checked,
- functionality has been verified.

---

# 6. Resume Rules

Whenever Claude Code starts a new session:

### Step 1

Read:

```text
CLAUDE.md
```

### Step 2

Determine:

```text
Completed tasks
In-progress tasks
Pending tasks
Next recommended task
```

### Step 3

Inspect the current repository state.

### Step 4

Continue from the **first appropriate incomplete task**.

Do not restart completed work.

Do not recreate existing functionality.

Do not assume that previous plans were completed merely because they are listed in documentation.

Verify the repository state.

At the end of every meaningful work session:

1. Update `CLAUDE.md`.
2. Mark completed tasks.
3. Record incomplete work.
4. Record important technical decisions.
5. Set `Next Recommended Task`.

This ensures another Claude Code session can continue without losing context.

---

# PHASE 1 — AUDIT, ARCHITECTURE & PLANNING

## TASK-001 — Repository Audit

Inspect:

- Django configuration
- Applications
- Models
- URLs
- Views
- Serializers
- Forms
- Templates
- JavaScript
- CSS
- Static files
- Management commands
- Utility scripts
- Vocabulary-processing scripts
- Tests
- Requirements
- Environment configuration
- Deployment files
- Documentation

Do not modify functionality unnecessarily during this task.

Create a concise architecture report in:

```text
docs/ARCHITECTURE.md
```

---

## TASK-002 — Existing Feature Inventory

Create an inventory of:

### Working features

### Partially implemented features

### Broken features

### Missing features

### Technical debt

### Security concerns

### Performance concerns

Do not invent features that do not exist.

---

## TASK-003 — Architecture Documentation

Document the actual architecture.

At minimum:

```text
User
 ↓
Frontend
 ↓
Django
 ↓
Application Services
 ↓
Database
```

and:

```text
Vocabulary Source
 ↓
Extraction
 ↓
Cleaning
 ↓
Validation
 ↓
Deduplication
 ↓
Splitting
 ↓
Processing
 ↓
Vocabulary Lists
 ↓
Learning System
```

Document where each component currently exists in the repository.

---

## TASK-004 — Database Review

Inspect all current models.

Identify:

- relationships,
- indexes,
- constraints,
- duplicate data,
- inefficient relationships,
- missing timestamps,
- missing ownership relationships,
- unsafe fields,
- scalability concerns.

Do not redesign the database without understanding existing data and migrations.

---

## TASK-005 — Security Audit

Perform a security review before implementing major new functionality.

Check at minimum:

### Django security

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- CSRF
- CORS
- session security
- cookie security
- HTTPS
- security middleware
- clickjacking protection
- HSTS
- content security considerations

### Authentication

- password handling
- password reset
- session management
- authentication bypass
- brute-force protection

### Authorization

Verify that users can access only their own:

- learning progress
- sessions
- private data
- uploaded files

### File uploads

Protect against:

- malicious files
- oversized files
- unexpected file types
- path traversal
- unsafe filenames
- arbitrary file execution
- resource exhaustion

Never trust:

- filenames
- MIME types
- file extensions
- client-provided metadata

### APIs

Check:

- authentication
- authorization
- rate limiting
- input validation
- pagination
- object-level permissions
- excessive data exposure

### Database

Check:

- unsafe raw SQL
- injection risks
- unvalidated input
- mass assignment
- inefficient queries

### Frontend

Check:

- XSS
- unsafe HTML rendering
- exposed secrets
- unsafe URL handling
- sensitive data in JavaScript

### Secrets

Ensure secrets are not committed.

Check:

```text
.env
API keys
credentials
database passwords
production secrets
```

Use environment variables.

---

# PHASE 2 — BACKEND, DATA PIPELINE & LEARNING ENGINE

## TASK-006 — Vocabulary Data Architecture

Design or improve the vocabulary architecture.

Vocabulary should support information such as:

```text
word
pronunciation
part_of_speech
meaning
example
synonyms
antonyms
difficulty
source
```

Avoid unnecessary duplication.

Use normalized relationships where appropriate.

---

# TASK-007 — Vocabulary Import Pipeline

Build or improve:

```text
File
 ↓
Extraction
 ↓
Cleaning
 ↓
Validation
 ↓
Duplicate Detection
 ↓
Normalization
 ↓
Splitting
 ↓
Database
```

Support where appropriate:

- TXT
- CSV
- XLSX
- PDF

Existing project functionality should be reused where possible.

---

# TASK-008 — Automatic List Splitting

Large vocabulary datasets should be automatically divided into manageable lists.

Default:

```text
50 words per list
```

Example:

```text
3153 words

Part 1 — 50
Part 2 — 50
Part 3 — 50
...
Part 63 — 50
Part 64 — 3
```

A list must remain independently usable.

The implementation must avoid loading unnecessarily large datasets into memory when possible.

---

# TASK-009 — Background Processing

Large imports must not block normal web requests.

Implement or improve asynchronous/background processing where appropriate.

Processing should provide states such as:

```text
Pending
Processing
Completed
Failed
```

Track:

```text
progress
processed_items
total_items
error_count
started_at
completed_at
error_message
```

A completed list should become available without requiring the entire dataset to finish processing.

---

# TASK-010 — Learning State

Track learning progress per user and vocabulary item.

Suggested states:

```text
NEW
LEARNING
REVIEW
KNOWN
MASTERED
```

Track:

```text
times_seen
times_reviewed
times_known
times_failed
last_seen
last_reviewed
next_review
```

Do not delete vocabulary from the system when a user marks it as known.

---

# TASK-011 — Review Algorithm

Implement a modular review system.

The system should favor words that the learner struggles with.

Words consistently recognized should appear less frequently.

Consider:

- performance history
- review frequency
- previous failures
- last review time
- current learning state

Keep the algorithm isolated in a service/module so it can later be replaced by a more advanced spaced-repetition algorithm.

Do not unnecessarily claim that the system uses AI unless actual AI functionality exists.

---

# TASK-012 — Learning Sessions

Track:

- session start
- session end
- words attempted
- words known
- words requiring review
- duration
- accuracy

Provide a session summary.

---

# TASK-013 — API Layer

Review and improve APIs for:

```text
Authentication
Vocabulary collections
Lists
Words
Learning sessions
Progress
Review queue
Statistics
Uploads
Processing status
```

Use proper HTTP methods.

Validate all inputs.

Implement consistent error responses.

Do not expose internal stack traces.

---

# PHASE 3 — LEARNING EXPERIENCE & FRONTEND

## TASK-014 — Learning Interface

Build/refine the primary learning screen.

One vocabulary item should be the primary focus.

Display:

```text
WORD

Pronunciation

Part of Speech

Meaning

Example Sentence
```

Additional information should not overwhelm the user.

---

# TASK-015 — Swipe Interaction

Implement touch-friendly swipe interaction.

Support:

```text
Swipe Left
Swipe Right
Swipe Up
```

The exact meaning of each gesture must be clearly documented in the UI.

Also provide buttons for users who cannot or do not want to swipe.

Do not make gestures the only method of interaction.

---

# TASK-016 — Desktop Controls

Support:

```text
←
→
↑
Space
```

where appropriate.

Make keyboard controls accessible and discoverable.

---

# TASK-017 — Dashboard

Create a focused dashboard containing:

- vocabulary collections
- current progress
- words learned
- words remaining
- review words
- completed lists
- recent sessions
- daily activity
- streak

Do not add statistics simply for decoration.

Every metric should have a purpose.

---

# TASK-018 — Progress Visualization

Provide simple visualizations for:

- learning progress
- completion
- review activity
- session performance

Avoid unnecessary charts.

---

# TASK-019 — Responsive Design

Ensure the application works properly on:

- mobile
- tablet
- laptop
- desktop

Mobile interaction is particularly important because swipe learning is central to the product.

---

# TASK-020 — Accessibility

Implement:

- semantic HTML
- keyboard navigation
- visible focus
- sufficient contrast
- accessible buttons
- meaningful labels
- screen-reader-compatible controls

---

# PHASE 4 — SECURITY, TESTING, PERFORMANCE & PRODUCTION

## TASK-021 — Authentication Security

Verify:

- secure password storage
- password reset security
- session security
- CSRF protection
- login abuse protection
- rate limiting
- account enumeration considerations

---

# TASK-022 — Authorization Security

Verify object-level permissions.

A user must never be able to access another user's:

```text
Progress
Sessions
Private vocabulary data
Uploads
Account information
```

Test authorization explicitly.

---

# TASK-023 — Upload Security

Implement defense-in-depth for file uploads.

Requirements:

- maximum file size
- allowed extensions
- content validation
- safe filenames
- isolated upload directories
- path traversal protection
- no executable uploads
- processing time/resource limits

Never trust client-side validation.

---

# TASK-024 — API Security

Implement:

- authentication
- authorization
- rate limiting
- pagination
- input validation
- safe error handling
- object-level permissions

Prevent:

- IDOR
- injection
- excessive data exposure
- abuse of expensive endpoints

---

# TASK-025 — Django Production Security

Review production settings.

Ensure secrets are environment-based.

Review:

```text
DEBUG
SECRET_KEY
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
SECURE_SSL_REDIRECT
SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE
SECURE_HSTS_SECONDS
SECURE_CONTENT_TYPE_NOSNIFF
X_FRAME_OPTIONS
```

Only enable settings appropriate for the actual deployment environment.

Do not blindly copy security settings without understanding their effect.

---

# TASK-026 — Dependency Security

Review dependencies.

Identify:

- outdated packages
- vulnerable packages
- unnecessary packages

Do not upgrade dependencies blindly.

Check compatibility before upgrading.

---

# TASK-027 — Database Performance

Inspect:

- N+1 queries
- missing indexes
- unnecessary queries
- inefficient filtering
- unnecessary serialization
- large querysets

Use:

```text
select_related
prefetch_related
indexes
pagination
bulk operations
```

where appropriate.

---

# TASK-028 — Testing

Build a meaningful test suite.

Test:

### Models

- constraints
- relationships
- states

### Vocabulary processing

- TXT
- CSV
- XLSX
- PDF
- duplicates
- malformed data
- empty files
- 50-word boundary
- large datasets

### Learning

- state transitions
- progress
- review scheduling
- sessions

### API

- authentication
- authorization
- validation
- errors
- rate limits

### Security

- unauthorized access
- IDOR
- malicious uploads
- path traversal
- CSRF
- injection attempts

---

# TASK-029 — Performance Testing

Test large vocabulary imports.

Test:

```text
50 words
500 words
5,000 words
10,000+ words
```

Measure:

- processing time
- memory usage
- database performance
- API response time

Optimize only where evidence indicates a bottleneck.

---

# TASK-030 — Deployment

Verify deployment configuration.

The application should support a production environment using:

```text
Gunicorn
WhiteNoise
PostgreSQL
Environment variables
HTTPS
```

Ensure:

- static files work
- migrations work
- database connection works
- health checks work
- logs are useful
- secrets are not exposed

---

# TASK-031 — Documentation

Maintain:

```text
README.md
CLAUDE.md
docs/ARCHITECTURE.md
docs/SECURITY.md
docs/API.md
docs/DEPLOYMENT.md
```

Documentation must describe the actual implementation, not an imagined future architecture.

---

# 7. Engineering Rules

## Rule 1 — Inspect Before Editing

Never make large changes before understanding the relevant existing implementation.

---

## Rule 2 — Preserve Working Functionality

Do not rewrite functioning features merely because you prefer another architecture.

---

## Rule 3 — Small, Verifiable Changes

Prefer incremental changes.

After each logical group:

1. Run tests.
2. Check migrations.
3. Check application startup.
4. Review changed files.
5. Update documentation.

---

## Rule 4 — Security by Default

Treat all external input as untrusted.

This includes:

- users
- uploaded files
- API requests
- query parameters
- form data
- headers
- filenames
- imported vocabulary

---

## Rule 5 — No Secrets in Git

Never commit secrets.

If secrets are found in the repository:

1. Report them.
2. Remove them from source where appropriate.
3. Add proper environment configuration.
4. Explain that previously committed secrets may need rotation.

Do not expose secret values in documentation.

---

## Rule 6 — Do Not Overengineer

Do not introduce:

- unnecessary microservices
- unnecessary message queues
- unnecessary AI
- unnecessary dependencies
- unnecessary abstractions

Use the simplest architecture that reliably solves the problem.

---

## Rule 7 — Do Not Claim Completion Without Verification

A task can only be marked:

```text
[x]
```

when it has been implemented and verified.

---

# 8. Completion Protocol

At the end of every task:

### 1. Verify

Run relevant tests/checks.

### 2. Update CLAUDE.md

Update:

```text
Completed Tasks
In Progress
Pending Tasks
Known Issues
Next Recommended Task
```

### 3. Summarize

Provide:

```text
Task completed:
Files changed:
Tests performed:
Security checks:
Remaining issues:
Next task:
```

---

# 9. Session Startup Protocol

Whenever Claude Code starts working on VocabSwipe:

```text
1. Read CLAUDE.md.
2. Inspect git status.
3. Identify current branch.
4. Identify incomplete tasks.
5. Identify the Next Recommended Task.
6. Inspect relevant existing code.
7. Continue from that point.
```

Do not ask the user to explain the project again if the information is already documented in `CLAUDE.md`.

---

# 10. Git Safety

Before destructive operations:

- inspect git status
- inspect relevant files
- understand existing changes

Never:

```text
git reset --hard
git clean -fd
delete migrations
delete user data
```

unless explicitly instructed.

Do not overwrite the user's uncommitted work.

---

# 11. Definition of Done

VocabSwipe is considered production-ready only when:

- [ ] Core learning flow works
- [ ] Vocabulary processing works
- [ ] Large datasets can be processed safely
- [ ] 50-word splitting works correctly
- [ ] Background processing works
- [ ] Learning progress is persistent
- [ ] Review functionality works
- [ ] Authentication is secure
- [ ] Authorization is enforced
- [ ] Upload security is implemented
- [ ] APIs are validated and protected
- [ ] Rate limiting exists where necessary
- [ ] Tests cover critical functionality
- [ ] Performance has been checked
- [ ] Production configuration is secure
- [ ] Documentation is current
- [ ] CLAUDE.md accurately represents project state

---

# 12. First Action

Do not immediately start implementing every feature.

Your first task is:

**Audit the existing VocabSwipe repository.**

Then:

1. Create/update `CLAUDE.md`.
2. Create `docs/ARCHITECTURE.md`.
3. Create the complete task checklist.
4. Mark only genuinely completed tasks.
5. Identify the highest-priority incomplete task.
6. Begin implementation from there.

At the end of the audit, clearly state:

```text
Repository audit completed.

CLAUDE.md created/updated.

Architecture documented.

Task roadmap created.

Next task: TASK-XXX
```

Then continue with the next task if the user has asked you to proceed.

---

# Final Principle

VocabSwipe should evolve as a **real software product**, not as a collection of disconnected AI-generated features.

Every change must fit the existing architecture.

Every feature must have a clear purpose.

Every security-sensitive operation must be treated defensively.

Every completed task must be recorded.

Every future Claude Code session must be able to read `CLAUDE.md` and immediately understand:

> **What VocabSwipe is, what has already been done, what is currently being worked on, what remains, why decisions were made, and exactly where development should continue.**
