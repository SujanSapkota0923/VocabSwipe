# Browser viewport check

`viewport_check.js` is the tester's tool for UI tasks. It is not part of
`manage.py test` and adds nothing to `requirements.txt`: it needs Node and
`playwright-core`, installed outside the project.

It checks every page at 320, 375, 390 and 430 px, 768×1024 and 1280×800 for
horizontal overflow, and plays the game: no page scroll, controls on screen,
swipe reveals and saves, Next / arrow keys / Space / buttons, double-tap
guard, timer mode, finish screen, list menu, console errors. Screenshots land
in `tests/ui/shots/` (git-ignored) — look at them; a pass is not the same as
"looks right".

## Run

```bash
# one-time, outside the repo
mkdir -p ~/.cache/vocabswipe-ui && cd ~/.cache/vocabswipe-ui
npm init -y && npm install playwright-core && npx playwright install chromium
cd -

# throwaway database with demo data
export UI_DB=/tmp/vocabswipe-ui.sqlite3
rm -f $UI_DB*
DJANGO_DEBUG=1 DJANGO_DB_PATH=$UI_DB python manage.py migrate
DJANGO_DEBUG=1 DJANGO_DB_PATH=$UI_DB python manage.py shell < tests/ui/seed_ui_db.py
DJANGO_DEBUG=1 DJANGO_DB_PATH=$UI_DB python manage.py runserver 127.0.0.1:8123 &

NODE_PATH=~/.cache/vocabswipe-ui/node_modules node tests/ui/viewport_check.js        # all sizes
NODE_PATH=~/.cache/vocabswipe-ui/node_modules node tests/ui/viewport_check.js 320    # one size
```

It prints `NO PROBLEMS` and exits 0, or lists each problem and exits 1.

Optional settings: `BASE_URL`, `BIG_LIST`, `SMALL_LIST`, `UI_USER`,
`UI_PASS`, `CHROME_PATH` (use an existing Chromium), `SHOTS_DIR`.

## Limits

Headless Chromium with mouse-driven pointer events. It does not cover iOS
Safari (safe areas, the collapsing address bar, rubber-band scrolling) or real
touch hardware; check those on a device before calling a UI task verified.
