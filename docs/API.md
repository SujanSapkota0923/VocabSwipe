# API

All endpoints are in `vocab/urls.py` and `vocab/views.py`. Authentication is
Django's session cookie. POST requests need the CSRF token (`X-CSRFToken`
header for JSON, `csrfmiddlewaretoken` field for forms). There is no
versioning, pagination or rate limiting.

Path ids (`<id>`) use a custom converter: 1–18 digits, no leading zero.
Anything else, including ids too large for the database, is a 404.

## JSON endpoints

### `GET /api/cards/`

Cards to play. Open to guests.

| Query | Meaning |
| --- | --- |
| `list_id` | One list. Must be playable by the caller (`can_play`), otherwise the result is empty. A value that is not a positive integer returns `400 {"status":"error","message":"Invalid list_id"}`. |
| `review_mode=true` | Signed-in only: drop known words whose `next_review_date` is in the future. |

Without `list_id`: every list the user owns or joined; for a guest, lists
unlocked in this session.

Response `200`, a JSON array in random order, not paginated:

```json
[{"id": 1, "word": "candid", "meanings": ["Honest and direct."],
  "example": "He gave a candid account.", "audio_url": null, "is_known": false}]
```

`is_known` is always `false` for guests; `game.js` fills it from `localStorage`.

### `POST /api/cards/<card_id>/status/`

Record one answer. Body: `{"is_known": true|false}`.

| Case | Response |
| --- | --- |
| Signed in, card playable | `200 {"status":"success","level":2,"interval":6,"next_review":"<iso>","streak":3}` |
| Guest | `200 {"status":"guest"}` — nothing stored |
| Card missing or not playable | `404 {"status":"error","message":"Card not found"}` |
| Body not JSON | `400 {"status":"error","message":"Invalid JSON"}` |
| Not POST | `405 {"status":"error","message":"Only POST allowed"}` |

Side effects: `WordProgress.apply_review` (SM-2) and `UserStats.update_streak`.

### `GET /api/lists/`

Login required (redirects to `/login/` otherwise). Lists the user owns or joined.

```json
[{"id": 4, "name": "PTE core", "share_code": "K7Q2ZP", "count": 812,
  "owned": true, "is_public": false, "processing_status": "completed"}]
```

Runs one count query per list.

### `GET /api/lists/<list_id>/progress/`

Meaning-lookup progress, polled every 3 s by `dashboard.js`. Requires
`can_play`.

```json
{"id": 4, "name": "PTE core", "status": "processing", "total_words": 812,
 "words_processed": 120, "progress_percentage": 14, "error_message": null}
```

`404 {"error":"Word list not found"}` when missing or not playable.

### `GET /api/user-stats/`

Login required.

```json
{"current_streak": 3, "longest_streak": 9, "total_reviews": 410,
 "last_review_date": "2026-09-25"}
```

## Page and form endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET, POST | `/` | — | Home; POST `code` unlocks a list and redirects to the game. Signed-in users are redirected to the dashboard. |
| GET | `/explore/?q=` | — | Public lists, name/description search |
| GET, POST | `/dashboard/` | login | POST `action=join` (field `code`) or `action=upload` (fields `name`, `description`, `file`, `is_public`) |
| GET, POST | `/lists/<id>/settings/` | owner | Edit name, description, public flag |
| POST | `/lists/<id>/visibility/` | owner | Toggle public |
| POST | `/lists/<id>/delete/` | owner | Delete list and its words |
| POST | `/lists/<id>/leave/` | login | Remove a joined list |
| GET | `/game/` | — | `list_id`, `mode=classic\|timer`, `seconds=3..120`, `review_mode=true`, or `code=` to unlock and redirect |
| GET, POST | `/login/` | — | Django `LoginView` |
| POST | `/logout/` | — | Django `LogoutView` |
| GET, POST | `/signup/` | — | Create account and sign in |
| — | `/admin/` | staff | Django admin |

Owner-only views return 404 (settings) or silently redirect (visibility,
delete) for non-owners.

## Known gaps

Tracked in `Plan.md` (TASK-013, TASK-024): input validation for IDs, uniform
error format across endpoints, pagination for `/api/cards/`, rate limits, and
the N+1 count in `/api/lists/`.
